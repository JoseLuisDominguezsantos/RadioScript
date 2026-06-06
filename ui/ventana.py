# ─── RadioScript · ui/ventana.py ─────────────────────────────────────────────
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from tkinterdnd2 import TkinterDnD
from config import *
from ui.drop_zone    import DropZone
from ui.lista_audios import ListaAudios
from ui.transcriptor import Transcriptor
from ui.procesador   import Procesador, leer_api_key, guardar_api_key
from utils.archivos  import procesar_paths
from ui.ventana_patrones.ventana_principal import VentanaPatrones
from db.repositorios.transcripciones import TranscripcionesRepo
import os


class Ventana(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NOMBRE)
        self.geometry("880x680")
        self.minsize(700, 560)
        self.configure(bg=BG_DARK)

        self.audios: dict      = {}
        self._transcriptor     = Transcriptor()
        self._procesador       = Procesador()
        self._fuentes          = self._crear_fuentes()
        self._total_pendientes = 0
        self._completados      = 0
        self._reportes         = []   # lista de resultados procesados
        self._modo_ia          = tk.StringVar(value="auto")
        self._build()

        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - (880 // 2)
        y = (self.winfo_screenheight() // 2) - (680 // 2)
        self.geometry(f"880x680+{x}+{y}")

    # ─── Fuentes ──────────────────────────────────────────────────────────────
    def _crear_fuentes(self) -> dict:
        return {
            "title": font.Font(family="DejaVu Sans", size=18, weight="bold"),
            "sub":   font.Font(family="DejaVu Sans Mono", size=9),
            "label": font.Font(family="DejaVu Sans", size=10, weight="bold"),
            "body":  font.Font(family="DejaVu Sans", size=10),
            "small": font.Font(family="DejaVu Sans", size=8),
            "icon":  font.Font(family="DejaVu Sans", size=20),
        }

    # ─── Layout ───────────────────────────────────────────────────────────────
    def _build(self):
        self._header()
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, padx=24, pady=(12, 0))
        self._zona_arrastre()
        self._barra_info()
        self._lista()
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, padx=24)
        self._footer()

    def _header(self):
        h = tk.Frame(self, bg=BG_DARK)
        h.pack(fill=tk.X, padx=24, pady=(20, 0))
        tk.Label(h, text=APP_NOMBRE, font=self._fuentes["title"],
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        tk.Label(h, text=f" {APP_VERSION} ", font=self._fuentes["small"],
                 bg=ACCENT_BLUE, fg="white").pack(side=tk.LEFT, padx=(10, 0), pady=6)
        tk.Label(h, text=APP_SUBTITULO, font=self._fuentes["sub"],
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=14, pady=8)

    def _zona_arrastre(self):
        self.drop_zone = DropZone(
            self,
            on_archivos=self._agregar_archivos,
            on_abrir=self._abrir_archivos,
            fuentes=self._fuentes
        )
        self.drop_zone.pack(fill=tk.X, padx=24, pady=16)

    def _barra_info(self):
        barra = tk.Frame(self, bg=BG_DARK)
        barra.pack(fill=tk.X, padx=24, pady=(0, 6))
        self.lbl_contador = tk.Label(barra, text="0 archivos cargados",
                                     font=self._fuentes["small"],
                                     bg=BG_DARK, fg=TEXT_MUTED)
        self.lbl_contador.pack(side=tk.LEFT)

        btn_limpiar = tk.Label(barra, text=f"{ICONO_BASURA}  Eliminar todo",
                               font=self._fuentes["small"],
                               bg=BG_DARK, fg=ACCENT_RED, cursor="hand2")
        btn_limpiar.pack(side=tk.RIGHT)
        btn_limpiar.bind("<Button-1>", lambda e: self._confirmar_limpiar())
        btn_limpiar.bind("<Enter>",    lambda e: btn_limpiar.configure(fg="#ff6b6b"))
        btn_limpiar.bind("<Leave>",    lambda e: btn_limpiar.configure(fg=ACCENT_RED))

    def _lista(self):
        self.lista = ListaAudios(
            self,
            on_eliminar=self._eliminar_audio,
            fuentes=self._fuentes
        )
        self.lista.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 8))

    def _footer(self):
        footer = tk.Frame(self, bg=BG_DARK)
        footer.pack(fill=tk.X, padx=24, pady=(8, 10))

        # ── Fila superior: estado + botones ──
        fila_top = tk.Frame(footer, bg=BG_DARK)
        fila_top.pack(fill=tk.X)

        self.lbl_estado = tk.Label(fila_top, text="Listo",
                                   font=self._fuentes["small"],
                                   bg=BG_DARK, fg=TEXT_MUTED)
        self.lbl_estado.pack(side=tk.LEFT)

        self.lbl_porcentaje = tk.Label(fila_top, text="",
                                       font=self._fuentes["small"],
                                       bg=BG_DARK, fg=ACCENT_BLUE)
        self.lbl_porcentaje.pack(side=tk.LEFT, padx=(10, 0))

        # ── Botón Ver Reportes ──
        self.btn_ver_reportes = tk.Label(
            fila_top, text="📄  Ver Reportes",
            font=self._fuentes["label"],
            bg=ACCENT_GREEN, fg="white",
            padx=16, pady=8, cursor="hand2"
        )
        self.btn_ver_reportes.bind("<Button-1>", lambda e: self._abrir_reportes())
        self.btn_ver_reportes.bind("<Enter>",    lambda e: self.btn_ver_reportes.configure(bg="#5dd879"))
        self.btn_ver_reportes.bind("<Leave>",    lambda e: self.btn_ver_reportes.configure(bg=ACCENT_GREEN))
        # Se muestra/oculta con _actualizar_btn_reportes()

        # ── Selector de IA ──
        frame_ia = tk.Frame(fila_top, bg=BG_DARK)
        frame_ia.pack(side=tk.RIGHT, padx=(0, 10))

        tk.Label(frame_ia, text="IA:",
                 font=self._fuentes["small"],
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 4))

        for modo, texto, color in [
            ("auto",     "Auto",     ACCENT_BLUE),
            ("deepseek", "DeepSeek", "#6c5ce7"),
            ("local",    "Local",    ACCENT_YELLOW),
        ]:
            rb = tk.Radiobutton(
                frame_ia, text=texto,
                variable=self._modo_ia, value=modo,
                font=self._fuentes["small"],
                bg=BG_DARK, fg=TEXT_MUTED,
                selectcolor=BG_DARK,
                activebackground=BG_DARK,
                indicatoron=0,
                padx=8, pady=4,
                relief="flat",
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=1)

        # Botón configurar key
        btn_key = tk.Label(frame_ia, text="🔑",
                           font=self._fuentes["small"],
                           bg=BG_ITEM, fg=TEXT_MUTED,
                           padx=6, pady=4, cursor="hand2")
        btn_key.pack(side=tk.LEFT, padx=(4, 0))
        btn_key.bind("<Button-1>", lambda e: self._configurar_key())
        btn_key.bind("<Enter>",    lambda e: btn_key.configure(bg=BG_HOVER))
        btn_key.bind("<Leave>",    lambda e: btn_key.configure(bg=BG_ITEM))

        # ── Botón Patrones ──
        btn_patrones = tk.Label(
            fila_top, text="⚙️  Patrones",
            font=self._fuentes["label"],
            bg="#6c5ce7", fg="white",
            padx=16, pady=8, cursor="hand2"
        )
        btn_patrones.pack(side=tk.RIGHT, padx=(0, 10))
        btn_patrones.bind("<Button-1>", lambda e: VentanaPatrones(self))
        btn_patrones.bind("<Enter>",    lambda e: btn_patrones.configure(bg="#8c7ae6"))
        btn_patrones.bind("<Leave>",    lambda e: btn_patrones.configure(bg="#6c5ce7"))

        # ── Botón Procesar ──
        self.btn_procesar = tk.Label(
            fila_top, text="🧠  Procesar",
            font=self._fuentes["label"],
            bg=ACCENT_YELLOW, fg="#0d1117",
            padx=16, pady=8, cursor="hand2"
        )
        self.btn_procesar.pack(side=tk.RIGHT, padx=(0, 10))
        self.btn_procesar.bind("<Button-1>", lambda e: self._iniciar_procesamiento())
        self.btn_procesar.bind("<Enter>",    lambda e: self._hover_procesar(True))
        self.btn_procesar.bind("<Leave>",    lambda e: self._hover_procesar(False))

        # ── Botón Transcribir ──
        self.btn_transcribir = tk.Label(
            fila_top, text=f"{ICONO_RAYO}  Transcribir",
            font=self._fuentes["label"],
            bg=ACCENT_BLUE, fg="white",
            padx=16, pady=8, cursor="hand2"
        )
        self.btn_transcribir.pack(side=tk.RIGHT, padx=(0, 10))
        self.btn_transcribir.bind("<Button-1>", lambda e: self._iniciar_transcripcion())
        self.btn_transcribir.bind("<Enter>",    lambda e: self._hover_btn(True))
        self.btn_transcribir.bind("<Leave>",    lambda e: self._hover_btn(False))

        # ── Barra de progreso global ──
        self.frame_progreso = tk.Frame(footer, bg=BG_DARK)
        self.frame_progreso.pack(fill=tk.X, pady=(8, 0))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Radio.Horizontal.TProgressbar",
                        troughcolor=BG_CARD,
                        background=ACCENT_BLUE,
                        bordercolor=BORDER,
                        lightcolor=ACCENT_BLUE,
                        darkcolor=ACCENT_BLUE,
                        thickness=8)
        style.configure("Proceso.Horizontal.TProgressbar",
                        troughcolor=BG_CARD,
                        background=ACCENT_YELLOW,
                        bordercolor=BORDER,
                        lightcolor=ACCENT_YELLOW,
                        darkcolor=ACCENT_YELLOW,
                        thickness=8)

        self.barra_global = ttk.Progressbar(
            self.frame_progreso,
            style="Radio.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL,
            length=100,
            mode="determinate",
            maximum=100,
            value=0
        )
        self.barra_global.pack(fill=tk.X)
        self.frame_progreso.pack_forget()

    # ─── Acciones ─────────────────────────────────────────────────────────────
    def _abrir_archivos(self):
        directorio = os.path.expanduser("~/Descargas")
        if not os.path.exists(directorio):
            directorio = os.path.expanduser("~/Downloads")
        archivos = filedialog.askopenfilenames(
            title="Seleccionar audios",
            initialdir=directorio,
            filetypes=[
                ("Archivos de audio", "*.ogg *.mp3 *.wav *.m4a *.opus *.flac"),
                ("Todos los archivos", "*.*")
            ]
        )
        if archivos:
            self._agregar_archivos(list(archivos))

    def _agregar_archivos(self, paths: list):
        resultado = procesar_paths(paths, self.audios)
        for path in resultado["paths_nuevos"]:
            self.audios[path] = {
                "nombre":        os.path.basename(path),
                "tamaño":        os.path.getsize(path),
                "estado":        "pendiente",
                "transcripcion": None,
                "informe":       None,
            }
        self.lista.actualizar(self.audios)
        self._actualizar_contador(resultado)

    def _eliminar_audio(self, path: str):
        if path in self.audios:
            del self.audios[path]
            self.lista.actualizar(self.audios)
            self._actualizar_contador()

    def _confirmar_limpiar(self):
        if not self.audios:
            return
        if messagebox.askyesno(
            "Eliminar todo",
            f"¿Eliminar los {len(self.audios)} audios de la lista?\n\nEsto no borra los archivos del disco.",
            icon="warning"
        ):
            self.audios.clear()
            self.lista.actualizar(self.audios)
            self._actualizar_contador()

    # ─── Transcripción ────────────────────────────────────────────────────────
    def _iniciar_transcripcion(self):
        if self._transcriptor.ocupado or self._procesador.ocupado:
            return

        pendientes = [p for p, i in self.audios.items()
                      if i.get("estado") == "pendiente"]
        if not pendientes:
            self._flash_estado("No hay audios pendientes", ACCENT_YELLOW)
            return

        self._total_pendientes = len(pendientes)
        self._completados      = 0
        self._btn_transcribir_estado(activo=False)
        self._btn_procesar_estado(activo=False)
        self._mostrar_barra_global(True, estilo="Radio.Horizontal.TProgressbar")
        self._actualizar_barra_global(0)

        self._transcriptor.transcribir_pendientes(
            audios       = self.audios,
            on_inicio    = self._cb_inicio,
            on_progreso  = self._cb_progreso,
            on_terminado = self._cb_terminado
        )

    def _cb_inicio(self, path):
        self.after(0, lambda: self._marcar_procesando(path))

    def _cb_progreso(self, path, texto, error=None):
        self.after(0, lambda: self._marcar_resultado(path, texto, error))

    def _cb_terminado(self):
        self.after(0, self._transcripcion_terminada)

    def _marcar_procesando(self, path):
        if path in self.audios:
            self.audios[path]["estado"] = "procesando"
            nombre = self.audios[path]["nombre"]
            self.lbl_estado.configure(
                text=f"{ICONO_ESPERA} Transcribiendo: {nombre}",
                fg=ACCENT_YELLOW)
            self.lista.actualizar(self.audios)

    def _marcar_resultado(self, path, texto, error=None):
        if path not in self.audios:
            return
        if error:
            self.audios[path]["estado"] = "error"
        else:
            self.audios[path]["estado"]        = "listo"
            self.audios[path]["transcripcion"] = texto

            # Guardar en BD
            try:
                tid = TranscripcionesRepo.guardar_transcripcion(
                    audio_path=path,
                    texto=texto
                )
                self.audios[path]["transcripcion_id"] = tid
            except Exception:
                pass

        self._completados += 1
        pct = int((self._completados / self._total_pendientes) * 100)
        self._actualizar_barra_global(pct)
        self.lista.actualizar(self.audios)

    def _transcripcion_terminada(self):
        self._actualizar_barra_global(100)
        total = sum(1 for i in self.audios.values() if i["estado"] == "listo")
        self.lbl_estado.configure(
            text=f"{ICONO_OK} Completado — {total} audio(s) transcritos",
            fg=ACCENT_GREEN)
        self.lbl_porcentaje.configure(text="")
        self.after(3000, lambda: [
            self.lbl_estado.configure(text="Listo", fg=TEXT_MUTED),
            self._mostrar_barra_global(False)
        ])
        self._btn_transcribir_estado(activo=True)
        self._btn_procesar_estado(activo=True)

    # ─── Procesamiento ────────────────────────────────────────────────────────
    def _iniciar_procesamiento(self):
        if self._transcriptor.ocupado or self._procesador.ocupado:
            return

        procesables = [
            p for p, i in self.audios.items()
            if i.get("estado") == "listo"
            and i.get("transcripcion")
            and not i.get("informe")
        ]
        if not procesables:
            self._flash_estado("No hay reportes listos para procesar", ACCENT_YELLOW)
            return

        self._total_pendientes = len(procesables)
        self._completados      = 0
        self._btn_transcribir_estado(activo=False)
        self._btn_procesar_estado(activo=False)
        self._mostrar_barra_global(True, estilo="Proceso.Horizontal.TProgressbar")
        self._actualizar_barra_global(0)

        self._procesador.procesar_pendientes(
            audios       = self.audios,
            modo         = self._modo_ia.get(),
            on_inicio    = self._cb_proc_inicio,
            on_progreso  = self._cb_proc_progreso,
            on_terminado = self._cb_proc_terminado
        )

    def _cb_proc_inicio(self, path):
        self.after(0, lambda: self._marcar_procesando_ia(path))

    def _cb_proc_progreso(self, path, resultado, error=None):
        self.after(0, lambda: self._marcar_resultado_ia(path, resultado, error))

    def _cb_proc_terminado(self):
        self.after(0, self._procesamiento_terminado)

    def _marcar_procesando_ia(self, path):
        if path in self.audios:
            nombre = self.audios[path]["nombre"]
            self.lbl_estado.configure(
                text=f"🧠 Procesando con IA: {nombre}",
                fg=ACCENT_YELLOW)

    def _marcar_resultado_ia(self, path, resultado, error=None):
        if path not in self.audios:
            return
        if resultado and not error:
            self.audios[path]["informe"]   = resultado.get("informe", "")
            self.audios[path]["resultado"] = resultado
            self._reportes.append({
                "path":             path,
                "nombre_audio":     self.audios[path]["nombre"],
                "transcripcion":    self.audios[path].get("transcripcion", ""),
                "transcripcion_id": self.audios[path].get("transcripcion_id"),
                "paciente_id":      None,
                "resultado":        resultado,
                "guardado":         False,
            })
        else:
            self.audios[path]["informe"] = f"[Error IA: {error}]"

        self._completados += 1
        pct = int((self._completados / self._total_pendientes) * 100)
        self._actualizar_barra_global(pct)

    def _procesamiento_terminado(self):
        self._actualizar_barra_global(100)
        total = len(self._reportes)
        self.lbl_estado.configure(
            text=f"{ICONO_OK} {total} reporte(s) procesado(s) — pulsa 'Ver Reportes'",
            fg=ACCENT_GREEN)
        self.lbl_porcentaje.configure(text="")
        self._btn_transcribir_estado(activo=True)
        self._btn_procesar_estado(activo=True)
        self._actualizar_btn_reportes()          # siempre actualizar botón
        self.after(500, lambda: self._mostrar_barra_global(False))
        self.after(4000, lambda: self.lbl_estado.configure(text="Listo", fg=TEXT_MUTED))

    def _configurar_key(self):
        """Diálogo para ingresar/actualizar la API key de OpenRouter."""
        from tkinter import simpledialog
        key_actual = leer_api_key()
        nueva_key = simpledialog.askstring(
            "API Key — OpenRouter",
            "Pega tu API key de OpenRouter (sk-or-...):\n"
            "Obtenerla en: openrouter.ai/keys",
            initialvalue=key_actual,
            parent=self
        )
        if nueva_key and nueva_key.strip():
            guardar_api_key(nueva_key.strip())
            self._flash_estado("✅ API key guardada correctamente", ACCENT_GREEN)

    def _actualizar_btn_reportes(self):
        """Muestra u oculta el botón Ver Reportes según si hay reportes.""";
        if self._reportes:
            self.btn_ver_reportes.pack(side=tk.RIGHT, padx=(0, 10))
        else:
            self.btn_ver_reportes.pack_forget()

    def _abrir_reportes(self):
        if not self._reportes:
            return
        from ui.ventana_reportes import VentanaReportes
        VentanaReportes(self, self._reportes)

    # ─── Estados de botones ───────────────────────────────────────────────────
    def _btn_transcribir_estado(self, activo: bool):
        if activo:
            self.btn_transcribir.configure(
                bg=ACCENT_BLUE, fg="white", cursor="hand2",
                text=f"{ICONO_RAYO}  Transcribir")
        else:
            self.btn_transcribir.configure(
                bg="#2d333b", fg=TEXT_MUTED, cursor="arrow",
                text=f"{ICONO_ESPERA}  Transcribiendo...")

    def _btn_procesar_estado(self, activo: bool):
        if activo:
            self.btn_procesar.configure(
                bg=ACCENT_YELLOW, fg="#0d1117", cursor="hand2",
                text="🧠  Procesar")
        else:
            self.btn_procesar.configure(
                bg="#2d333b", fg=TEXT_MUTED, cursor="arrow",
                text=f"{ICONO_ESPERA}  Procesando...")

    def _hover_btn(self, entrar: bool):
        if not self._transcriptor.ocupado:
            self.btn_transcribir.configure(
                bg="#4a9eff" if entrar else ACCENT_BLUE)

    def _hover_procesar(self, entrar: bool):
        if not self._procesador.ocupado:
            self.btn_procesar.configure(
                bg="#f0b429" if entrar else ACCENT_YELLOW)

    def _flash_estado(self, texto, color):
        self.lbl_estado.configure(text=texto, fg=color)
        self.after(2500, lambda: self.lbl_estado.configure(text="Listo", fg=TEXT_MUTED))

    # ─── Barra global ─────────────────────────────────────────────────────────
    def _actualizar_barra_global(self, valor: int):
        self.barra_global.configure(value=valor)
        if self._total_pendientes > 0:
            self.lbl_porcentaje.configure(
                text=f"{self._completados}/{self._total_pendientes}  {valor}%",
                fg=ACCENT_BLUE)

    def _mostrar_barra_global(self, mostrar: bool, estilo: str = "Radio.Horizontal.TProgressbar"):
        self.barra_global.configure(style=estilo)
        if mostrar:
            self.frame_progreso.pack(fill=tk.X, pady=(8, 0))
        else:
            self.frame_progreso.pack_forget()

    # ─── Contador ─────────────────────────────────────────────────────────────
    def _actualizar_contador(self, resultado: dict = None):
        total      = len(self.audios)
        texto_base = f"{total} archivo{'s' if total != 1 else ''} cargado{'s' if total != 1 else ''}"

        if resultado and (resultado.get("duplicados") or resultado.get("invalidos")):
            avisos = []
            if resultado["duplicados"]:
                d = resultado["duplicados"]
                avisos.append(f"{d} duplicado{'s' if d > 1 else ''} ignorado{'s' if d > 1 else ''}")
            if resultado["invalidos"]:
                avisos.append(f"{resultado['invalidos']} formato inválido")
            self.lbl_contador.configure(
                text=f"{texto_base}  ·  {ICONO_AVISO} {', '.join(avisos)}",
                fg=ACCENT_YELLOW)
            self.after(3500, lambda: self.lbl_contador.configure(
                text=texto_base, fg=TEXT_MUTED))
        else:
            self.lbl_contador.configure(text=texto_base, fg=TEXT_MUTED)