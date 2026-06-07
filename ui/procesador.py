# ─── RadioScript · ui/procesador.py ─────────────────────────────────────────
import threading
import json
import re
import os
import urllib.request
import urllib.error
from db.conexion import Conexion


# ─── Configuración de modelos ─────────────────────────────────────────────────
OLLAMA_URL      = "http://localhost:11434/api/generate"
OPENROUTER_URL  = "https://openrouter.ai/api/v1/chat/completions"
MODELO_OLLAMA   = "llama3.1:8b"
MODELO_OLLAMA_FT= "radioscript"
MODELO_DEEPSEEK = "deepseek/deepseek-chat"
KEY_FILE        = os.path.expanduser("~/.radioscript/openrouter.key")


def leer_api_key() -> str:
    """Lee la API key de OpenRouter desde el archivo seguro."""
    try:
        with open(KEY_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return ""


def guardar_api_key(key: str):
    """Guarda la API key de forma segura."""
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, "w") as f:
        f.write(key.strip())
    os.chmod(KEY_FILE, 0o600)


def _modelo_ollama_activo() -> str:
    """Usa el modelo fine-tuneado si existe, si no el base."""
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            modelos = [m["name"].split(":")[0] for m in data.get("models", [])]
            if MODELO_OLLAMA_FT in modelos:
                return MODELO_OLLAMA_FT
    except Exception:
        pass
    return MODELO_OLLAMA


# ─── Vocabulario ──────────────────────────────────────────────────────────────
def _obtener_vocabulario() -> list:
    cur = Conexion.cursor()
    cur.execute("SELECT termino, variantes FROM vocabulario ORDER BY LENGTH(termino) DESC")
    resultado = cur.fetchall()
    cur.close()
    return resultado


def _corregir_transcripcion(texto: str, vocabulario: list) -> str:
    texto_corregido = texto
    for row in vocabulario:
        termino   = row["termino"]
        variantes = row["variantes"] or ""
        for variante in [v.strip() for v in variantes.split(",") if v.strip()]:
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
        WHERE p.activo = 1 ORDER BY t.nombre
    """)
    resultado = cur.fetchall()
    cur.close()
    return resultado


def _obtener_ejemplos_bd(limite: int = 15) -> list:
    cur = Conexion.cursor()
    cur.execute("""
        SELECT transcripcion, informe_final, calidad
        FROM ejemplos_ia
        ORDER BY calidad DESC, id DESC
        LIMIT %s
    """, (limite,))
    resultado = cur.fetchall()
    cur.close()
    return resultado


def contar_ejemplos() -> dict:
    cur = Conexion.cursor()
    cur.execute("""
        SELECT calidad, COUNT(*) as total
        FROM ejemplos_ia
        GROUP BY calidad ORDER BY calidad DESC
    """)
    resultado = cur.fetchall()
    cur.close()
    total = sum(r["total"] for r in resultado)
    alta  = sum(r["total"] for r in resultado if r["calidad"] >= 7)
    return {"total": total, "alta_calidad": alta, "detalle": resultado}


# ─── Prompt compartido ────────────────────────────────────────────────────────
def _detectar_tipo_estudio(transcripcion: str, plantillas: list) -> dict | None:
    """Detecta qué plantilla usar basándose en palabras clave de la transcripción."""
    texto = transcripcion.upper()
    # Mapa de palabras clave → tipo de estudio
    keywords = {
        "TORAX": ["TORAX", "TÓRAX", "PECHO", "PA"],
        "ABDOMEN": ["ABDOMEN", "ABDOMINAL", "ABD"],
        "CERVICAL": ["CERVICAL", "CUELLO", "COLUMNA CERVICAL"],
        "DORSAL": ["DORSAL", "COLUMNA DORSAL", "DORSO"],
        "LUMBAR": ["LUMBAR", "COLUMNA LUMBAR", "LUMBARES"],
        "CRÁNEO": ["CRANEO", "CRÁNEO", "CRANEAL"],
        "HOMBRO": ["HOMBRO", "CLAVICULA", "CLAVÍCULA"],
        "CODO": ["CODO"],
        "MANO": ["MANO", "CARPO", "METACARPO"],
        "RODILLA": ["RODILLA"],
        "PIE": ["PIE", "TARSO", "METATARSO"],
        "TOBILLO": ["TOBILLO"],
        "PIERNA": ["PIERNA", "TIBIA", "PERONÉ"],
        "MUSLO": ["MUSLO", "FEMUR", "FÉMUR"],
        "PELVIS": ["PELVIS", "CADERA", "COXOFEMORAL"],
        "SENOS PARANASALES": ["SENOS", "PARANASALES", "SINUSAL"],
        "HISTEROSALPINGOGRAFIA": ["HISTEROSALPINGOGRAFIA", "TROMPA", "UTERO", "ÚTERO"],
    }
    for tipo_key, words in keywords.items():
        if any(w in texto for w in words):
            for p in plantillas:
                if tipo_key in p["tipo_estudio"].upper():
                    return p
    return None


def _construir_prompt(transcripcion_original: str,
                      transcripcion_corregida: str,
                      plantillas: list,
                      ejemplos: list) -> str:

    # Detectar plantilla más probable para reducir el contexto
    plantilla_detectada = _detectar_tipo_estudio(transcripcion_corregida, plantillas)

    seccion_ejemplos = ""
    if ejemplos:
        alta = [e for e in ejemplos if e.get("calidad", 5) >= 7]
        norm = [e for e in ejemplos if e.get("calidad", 5) < 7]
        seccion_ejemplos = "\nEJEMPLOS REALES:\n"
        for i, ej in enumerate((alta[:5] + norm[:3]), 1):
            seccion_ejemplos += f"\nEjemplo {i}:\nTRANSCRIPCIÓN: {ej['transcripcion']}\nINFORME:\n{ej['informe_final']}\n"
        seccion_ejemplos += "\n"

    # Si detectamos la plantilla, solo enviamos esa + lista de tipos
    # Si no, enviamos todas (fallback)
    tipos_lista = "\n".join(f"- {p['tipo_estudio']}" for p in plantillas)

    if plantilla_detectada:
        p = plantilla_detectada
        plantilla_ctx = f"""
TIPO DETECTADO: {p["tipo_estudio"]}
TÉCNICA: {p["tecnica"] or ""}
HALLAZGOS BASE (patrón normal completo):
{p["hallazgos_base"] or ""}
IMPRESIÓN DIAGNÓSTICA BASE:
{p["conclusion_base"] or ""}"""
        instruccion_tipo = f'El tipo de estudio ES: {p["tipo_estudio"]}'
    else:
        plantilla_ctx = "\n".join(
            f"=== {p['tipo_estudio']} ===\nTÉCNICA: {p['tecnica'] or ''}\nHALLAZGOS BASE:\n{p['hallazgos_base'] or ''}\n---"
            for p in plantillas
        )
        instruccion_tipo = f"Detecta el tipo de estudio entre:\n{tipos_lista}"

    nota = f"\nTRANSCRIPCIÓN CON TÉRMINOS CORREGIDOS:\n{transcripcion_corregida}\n" \
           if transcripcion_corregida != transcripcion_original else ""

    return f"""Eres un experto en radiología médica. Genera un informe radiológico formal.
{seccion_ejemplos}
PLANTILLA A USAR:
{plantilla_ctx}

TRANSCRIPCIÓN DEL AUDIO:
{transcripcion_original}
{nota}
INSTRUCCIONES:
1. {instruccion_tipo}
2. Copia TODAS las líneas del patrón base tal como están.
3. MODIFICA solo las líneas donde el médico dictó algo diferente.
4. Extrae nombre del paciente y edad de la transcripción.
5. IMPRESIÓN DIAGNÓSTICA: solo hallazgos ANORMALES que mencionó el médico.
   Sin hallazgos anormales → usa la conclusión base exacta.
   Con hallazgos anormales → lista cada uno + "RESTO SIN ENCUENTROS REMARCABLES."
6. Todo en MAYÚSCULAS.

JSON de respuesta (sin texto adicional):
{{
  "tipo_estudio": "tipo exacto",
  "nombre_paciente": "nombre o vacío",
  "edad": "edad o vacío",
  "fecha_estudio": "",
  "informe": "informe con \\n para saltos de línea"
}}"""


# ─── Llamadas a APIs ──────────────────────────────────────────────────────────
def _llamar_ollama(prompt: str) -> str:
    modelo = _modelo_ollama_activo()
    payload = json.dumps({
        "model": modelo, "prompt": prompt, "stream": False,
        "keep_alive": 0,
        "options": {"temperature": 0.1, "num_predict": 2000, "top_p": 0.9}
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", ""), modelo


def _llamar_deepseek(prompt: str) -> tuple:
    api_key = leer_api_key()
    if not api_key:
        raise ValueError("No hay API key de OpenRouter configurada.")

    payload = json.dumps({
        "model": MODELO_DEEPSEEK,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL, data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer":  "https://radioscript.local",
            "X-Title":       "RadioScript"
        }, method="POST")

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        texto = data["choices"][0]["message"]["content"]
        return texto, MODELO_DEEPSEEK


def _parsear_respuesta(texto: str) -> dict:
    texto = texto.strip()
    if "```" in texto:
        texto = texto.replace("```json", "").replace("```", "")
    inicio = texto.find("{")
    fin    = texto.rfind("}") + 1
    if inicio != -1 and fin > inicio:
        texto = texto[inicio:fin]
    return json.loads(texto)


# ─── Fine-tuning ──────────────────────────────────────────────────────────────
def exportar_datos_entrenamiento(ruta_jsonl: str) -> int:
    cur = Conexion.cursor()
    cur.execute("""
        SELECT transcripcion, informe_final FROM ejemplos_ia
        WHERE calidad >= 7 ORDER BY calidad DESC, id DESC
    """)
    ejemplos = cur.fetchall()
    cur.close()
    if not ejemplos:
        return 0
    with open(ruta_jsonl, "w", encoding="utf-8") as f:
        for ej in ejemplos:
            entrada = {
                "prompt": f"Transcripción de audio médico:\n{ej['transcripcion']}\n\nGenera el informe radiológico:",
                "response": ej["informe_final"]
            }
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return len(ejemplos)


def crear_modelfile(ruta_modelfile: str, ruta_jsonl: str):
    contenido = f"""FROM llama3.1:8b

SYSTEM \"\"\"Eres RadioScript, un asistente especializado en generar informes radiológicos formales.
Tu función es tomar transcripciones de audio dictadas por médicos radiólogos y convertirlas en
informes estructurados usando las plantillas base disponibles.\"\"\"

PARAMETER temperature 0.1
PARAMETER num_predict 2000
"""
    with open(ruta_modelfile, "w") as f:
        f.write(contenido)


# ─── Procesador principal ─────────────────────────────────────────────────────
class Procesador:
    def __init__(self):
        self._ocupado = False

    @property
    def ocupado(self):
        return self._ocupado

    def procesar_pendientes(self, audios: dict, modo: str,
                             on_inicio, on_progreso, on_terminado):
        """
        modo: 'local' → Ollama | 'deepseek' → DeepSeek | 'auto' → DeepSeek con fallback
        """
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
            ejemplos    = _obtener_ejemplos_bd(limite=15)
            vocabulario = _obtener_vocabulario()

            if not plantillas:
                for path in procesables:
                    on_progreso(path, None, error="No hay plantillas base configuradas.")
                self._ocupado = False
                on_terminado()
                return

            for path in procesables:
                on_inicio(path)
                transcripcion_orig = audios[path]["transcripcion"]
                transcripcion_cor  = _corregir_transcripcion(transcripcion_orig, vocabulario)
                try:
                    prompt = _construir_prompt(
                        transcripcion_orig, transcripcion_cor, plantillas, ejemplos)

                    texto, modelo_usado = self._llamar_con_modo(prompt, modo)
                    resultado = _parsear_respuesta(texto)
                    resultado["transcripcion_corregida"] = transcripcion_cor
                    resultado["modelo_usado"] = modelo_usado
                    print(f"[IA] Procesado con {modelo_usado}")
                    on_progreso(path, resultado)
                except Exception as e:
                    on_progreso(path, None, error=str(e))

            self._ocupado = False
            on_terminado()

        threading.Thread(target=_worker, daemon=True).start()

    def _llamar_con_modo(self, prompt: str, modo: str) -> tuple:
        if modo == "local":
            return _llamar_ollama(prompt)
        elif modo == "deepseek":
            return _llamar_deepseek(prompt)
        else:  # auto — DeepSeek con fallback a Ollama
            try:
                return _llamar_deepseek(prompt)
            except Exception as e:
                print(f"[DeepSeek] Fallo ({e}) — usando Ollama como respaldo")
                return _llamar_ollama(prompt)