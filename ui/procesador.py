# ─── RadioScript · ui/procesador.py ─────────────────────────────────────────
import threading
import json
import re
import urllib.request
from db.conexion import Conexion


OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO     = "llama3.1:8b"


# ─── Vocabulario ──────────────────────────────────────────────────────────────
def _obtener_vocabulario() -> list:
    """Devuelve todos los términos con sus variantes para corrección."""
    cur = Conexion.cursor()
    cur.execute("SELECT termino, variantes FROM vocabulario ORDER BY LENGTH(termino) DESC")
    resultado = cur.fetchall()
    cur.close()
    return resultado


def _corregir_transcripcion(texto: str, vocabulario: list) -> str:
    """
    Reemplaza variantes de Whisper por el término médico correcto.
    Ej: 'dextresco leosidorsal' → 'DEXTROESCOLIOSIS'
    """
    texto_corregido = texto
    for row in vocabulario:
        termino   = row["termino"]          # ej: DEXTROESCOLIOSIS
        variantes = row["variantes"] or ""  # ej: dextro escoliosis, dextrescoliosis

        # Dividir variantes por coma y limpiar
        lista_variantes = [v.strip() for v in variantes.split(",") if v.strip()]

        for variante in lista_variantes:
            # Reemplazo case-insensitive con palabra completa aproximada
            patron = re.compile(re.escape(variante), re.IGNORECASE)
            texto_corregido = patron.sub(termino, texto_corregido)

    return texto_corregido


# ─── BD ───────────────────────────────────────────────────────────────────────
def _obtener_plantillas_bd() -> list:
    cur = Conexion.cursor()
    cur.execute("""
        SELECT p.id, p.nombre, p.tecnica, p.hallazgos_base, p.conclusion_base,
               t.nombre AS tipo_estudio
        FROM plantillas p
        JOIN tipos_estudio t ON p.tipo_estudio_id = t.id
        WHERE p.activo = 1
        ORDER BY t.nombre
    """)
    resultado = cur.fetchall()
    cur.close()
    return resultado


def _obtener_ejemplos_bd(limite: int = 5) -> list:
    cur = Conexion.cursor()
    cur.execute("""
        SELECT transcripcion, informe_final
        FROM ejemplos_ia
        ORDER BY id DESC
        LIMIT %s
    """, (limite,))
    resultado = cur.fetchall()
    cur.close()
    return resultado


# ─── Prompt ───────────────────────────────────────────────────────────────────
def _construir_prompt(transcripcion_original: str,
                      transcripcion_corregida: str,
                      plantillas: list,
                      ejemplos: list) -> str:

    # Few-shot con ejemplos reales
    seccion_ejemplos = ""
    if ejemplos:
        seccion_ejemplos = "\nEJEMPLOS REALES (transcripción → informe corregido por el radiólogo):\n"
        for i, ej in enumerate(ejemplos, 1):
            seccion_ejemplos += f"""
--- Ejemplo {i} ---
TRANSCRIPCIÓN: {ej['transcripcion']}
INFORME CORRECTO:
{ej['informe_final']}
"""
        seccion_ejemplos += "\n"

    # Plantillas disponibles
    tipos_disponibles = "\n".join(f"- {p['tipo_estudio']}" for p in plantillas)
    plantillas_texto  = ""
    for p in plantillas:
        plantillas_texto += f"""
=== {p['tipo_estudio']} ===
TÉCNICA: {p['tecnica'] or ''}
HALLAZGOS BASE:
{p['hallazgos_base'] or ''}
IMPRESIÓN DIAGNÓSTICA BASE (cuando todo es normal):
{p['conclusion_base'] or ''}
---"""

    # Mostrar si hubo correcciones de vocabulario
    nota_correccion = ""
    if transcripcion_corregida != transcripcion_original:
        nota_correccion = f"\nTRANSCRIPCIÓN CORREGIDA (términos médicos normalizados):\n{transcripcion_corregida}\n"

    prompt = f"""Eres un experto en radiología médica. Genera un informe radiológico formal a partir de una transcripción de audio dictada por un médico.
{seccion_ejemplos}
TIPOS DE ESTUDIO DISPONIBLES:
{tipos_disponibles}

PLANTILLAS BASE:
{plantillas_texto}

TRANSCRIPCIÓN DEL AUDIO:
{transcripcion_original}
{nota_correccion}
REGLAS ESTRICTAS:
1. Detecta el tipo de estudio mencionado por el médico.
2. Usa la plantilla base como ESQUELETO — copia TODAS sus líneas.
3. MODIFICA solo las líneas donde el médico dictó algo diferente al patrón normal:
   - Si mencionó "dextroescoliosis dorsal alta" → AGREGA esa línea en HALLAZGOS
   - Si mencionó ICT = 44% → cambia "ICT NORMAL" por "ICT = 44%"
   - Si mencionó pulmones hiperinsuflados → modifica esa línea
4. Extrae nombre del paciente y edad de la transcripción (ignora ruido de Whisper).
5. IMPRESIÓN DIAGNÓSTICA: lista SOLO los hallazgos ANORMALES que mencionó el médico.
   - Si solo hay hallazgos normales → usa la conclusión base exacta.
   - Si hay hallazgos anormales → lista cada uno + "RESTO SIN ENCUENTROS REMARCABLES."
6. Todo en MAYÚSCULAS.
7. Formato exacto del informe:
   Nombre: [nombre]
   Edad:   [edad]

   TÉCNICA: [técnica]

   HALLAZGOS:
   [hallazgos uno por línea]

   IMPRESIÓN DIAGNÓSTICA:
   [conclusión]

Responde ÚNICAMENTE con JSON válido sin texto adicional:
{{
  "tipo_estudio": "tipo detectado",
  "nombre_paciente": "nombre o vacío",
  "edad": "edad o vacío",
  "fecha_estudio": "",
  "informe": "informe completo con \\n para saltos de línea"
}}"""
    return prompt


# ─── Ollama ───────────────────────────────────────────────────────────────────
def _llamar_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model":   MODELO,
        "prompt":  prompt,
        "stream":  False,
        "keep_alive": 0,   # libera la RAM inmediatamente al terminar
        "options": {
            "temperature": 0.1,
            "num_predict": 2000,
            "top_p": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def _parsear_respuesta(texto: str) -> dict:
    texto = texto.strip()
    if "```" in texto:
        texto = texto.replace("```json", "").replace("```", "")
    inicio = texto.find("{")
    fin    = texto.rfind("}") + 1
    if inicio != -1 and fin > inicio:
        texto = texto[inicio:fin]
    return json.loads(texto)


# ─── Procesador ───────────────────────────────────────────────────────────────
class Procesador:
    def __init__(self):
        self._ocupado = False

    @property
    def ocupado(self):
        return self._ocupado

    def procesar_pendientes(self, audios: dict,
                             on_inicio,
                             on_progreso,
                             on_terminado):
        procesables = [
            p for p, info in audios.items()
            if info.get("estado") == "listo"
            and info.get("transcripcion")
            and not info.get("informe")
        ]

        if not procesables:
            on_terminado()
            return

        self._ocupado = True

        def _worker():
            plantillas  = _obtener_plantillas_bd()
            ejemplos    = _obtener_ejemplos_bd(limite=5)
            vocabulario = _obtener_vocabulario()

            if not plantillas:
                for path in procesables:
                    on_progreso(path, None,
                                error="No hay plantillas base. "
                                      "Ve a Patrones → Plantilla Base y crea una.")
                self._ocupado = False
                on_terminado()
                return

            for path in procesables:
                on_inicio(path)
                transcripcion_original = audios[path]["transcripcion"]
                # Corregir vocabulario antes de enviar a la IA
                transcripcion_corregida = _corregir_transcripcion(
                    transcripcion_original, vocabulario
                )
                try:
                    prompt    = _construir_prompt(
                        transcripcion_original,
                        transcripcion_corregida,
                        plantillas,
                        ejemplos
                    )
                    respuesta = _llamar_ollama(prompt)
                    resultado = _parsear_respuesta(respuesta)
                    # Guardar también la transcripción corregida para referencia
                    resultado["transcripcion_corregida"] = transcripcion_corregida
                    on_progreso(path, resultado)
                except Exception as e:
                    on_progreso(path, None, error=str(e))

            self._ocupado = False
            on_terminado()

        threading.Thread(target=_worker, daemon=True).start()