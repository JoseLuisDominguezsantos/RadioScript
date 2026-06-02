# ─── RadioScript · ui/lista_audios.py ────────────────────────────────────────
import tkinter as tk
from tkinter import ttk
import os
from config import *
from utils.archivos import formato_tamaño


class ListaAudios(tk.Frame):
    """Lista scrolleable de audios con transcripción desplegable y barra de progreso por item."""

    def __init__(self, parent, on_eliminar, fuentes, **kwargs):
        super().__init__(parent, bg=BG_CARD,
                         highlightthickness=1,
                         highlightbackground=BORDER, **kwargs)
        self.on_eliminar = on_eliminar
        self.f           = fuentes
        self._expandidos = set()
        self._build()
        self._configurar_estilo()

    def _configurar_estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        # Barra del item activo — amarilla
        style.configure("Item.Horizontal.TProgressbar",
                        troughcolor=BG_DARK,
                        background=ACCENT_YELLOW,
                        bordercolor=BG_DARK,
                        lightcolor=ACCENT_YELLOW,
                        darkcolor=ACCENT_YELLOW,
                        thickness=3)

    def _build(self):
        self.canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL,
                                      command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.contenedor = tk.Frame(self.canvas, bg=BG_CARD)
        self._win = self.canvas.create_window((0, 0), window=self.contenedor,
                                              anchor="nw")
        self.contenedor.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",     self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>",    self._scroll)
        self.canvas.bind("<Button-4>",      self._scroll)
        self.canvas.bind("<Button-5>",      self._scroll)

        self._mostrar_vacio()

    # ─── Actualizar ──────────────────────────────────────────────────────────
    def actualizar(self, audios: dict):
        for w in self.contenedor.winfo_children():
            w.destroy()

        if not audios:
            self._expandidos.clear()
            self._mostrar_vacio()
            return

        self._expandidos = {p for p in self._expandidos if p in audios}

        for i, (path, info) in enumerate(audios.items()):
            self._crear_item(i, path, info)

    def _mostrar_vacio(self):
        tk.Label(self.contenedor,
                 text="No hay audios cargados aún",
                 font=self.f["body"], bg=BG_CARD, fg=TEXT_MUTED).pack(pady=40)

    # ─── Item ────────────────────────────────────────────────────────────────
    def _crear_item(self, indice, path, info):
        bg     = BG_ITEM if indice % 2 == 0 else BG_CARD
        estado = info.get("estado", "pendiente")

        wrapper = tk.Frame(self.contenedor, bg=bg,
                           highlightthickness=1,
                           highlightbackground=BORDER)
        wrapper.pack(fill=tk.X, padx=8, pady=3)

        # ── Fila principal ──
        fila = tk.Frame(wrapper, bg=bg)
        fila.pack(fill=tk.X)

        tk.Label(fila, text=ICONO_AUDIO, font=self.f["body"],
                 bg=bg, fg=ACCENT_BLUE).pack(side=tk.LEFT, padx=(12, 8), pady=10)

        info_frame = tk.Frame(fila, bg=bg)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=8)

        tk.Label(info_frame, text=info["nombre"],
                 font=self.f["label"], bg=bg, fg=TEXT_PRIMARY,
                 anchor="w").pack(fill=tk.X)

        detalles = f"{formato_tamaño(info['tamaño'])}  ·  {os.path.dirname(path)}"
        tk.Label(info_frame, text=detalles,
                 font=self.f["small"], bg=bg, fg=TEXT_MUTED,
                 anchor="w").pack(fill=tk.X)

        # Botón eliminar
        btn_x = tk.Label(fila, text=ICONO_ELIMINAR,
                         font=self.f["label"],
                         bg=ACCENT_RED, fg="white",
                         width=2, pady=6, cursor="hand2")
        btn_x.pack(side=tk.RIGHT, padx=(0, 10), pady=6)
        btn_x.bind("<Enter>",    lambda e: btn_x.configure(bg="#ff6b6b"))
        btn_x.bind("<Leave>",    lambda e: btn_x.configure(bg=ACCENT_RED))
        btn_x.bind("<Button-1>", lambda e, p=path: self.on_eliminar(p))

        # Badge estado
        colores = {"pendiente":  ACCENT_YELLOW,
                   "procesando": ACCENT_BLUE,
                   "listo":      ACCENT_GREEN,
                   "error":      ACCENT_RED}
        textos  = {"pendiente":  f"{ICONO_ESPERA} Pendiente",
                   "procesando": f"{ICONO_ESPERA} Procesando...",
                   "listo":      f"{ICONO_OK} Transcrito",
                   "error":      f"{ICONO_ERROR} Error"}

        tk.Label(fila, text=textos.get(estado, estado),
                 font=self.f["small"], bg=bg,
                 fg=colores.get(estado, TEXT_MUTED)).pack(side=tk.RIGHT, padx=8)

        # Botón desplegar (solo si transcrito)
        if estado == "listo" and info.get("transcripcion"):
            expandido = path in self._expandidos
            self._agregar_toggle(fila, wrapper, path, info, bg, expandido)

        # ── Barra de progreso del item (solo si procesando) ──
        if estado == "procesando":
            self._agregar_barra_item(wrapper, bg)

        # Hover
        for w in [fila, info_frame]:
            w.bind("<Enter>", lambda e, r=wrapper: r.configure(bg=BG_HOVER))
            w.bind("<Leave>", lambda e, r=wrapper, b=bg: r.configure(bg=b))

    def _agregar_barra_item(self, wrapper, bg):
        """Barra indeterminada animada mientras el item se procesa."""
        barra = ttk.Progressbar(
            wrapper,
            style="Item.Horizontal.TProgressbar",
            orient=tk.HORIZONTAL,
            mode="indeterminate",
            length=100
        )
        barra.pack(fill=tk.X, padx=12, pady=(0, 6))
        barra.start(15)   # velocidad de animación

    def _agregar_toggle(self, fila, wrapper, path, info, bg, expandido):
        icono_btn = "▲" if expandido else "▼"

        btn_toggle = tk.Label(fila, text=icono_btn,
                              font=self.f["small"],
                              bg=bg, fg=TEXT_ACCENT,
                              cursor="hand2", padx=6)
        btn_toggle.pack(side=tk.RIGHT, padx=(0, 4))

        panel     = tk.Frame(wrapper, bg="#0d1117")
        separador = tk.Frame(wrapper, bg=BORDER, height=1)

        if expandido:
            separador.pack(fill=tk.X, padx=12)
            panel.pack(fill=tk.X, padx=12, pady=(4, 10))
            self._llenar_panel(panel, info["transcripcion"])

        def _toggle(e=None):
            if path in self._expandidos:
                self._expandidos.discard(path)
                separador.pack_forget()
                panel.pack_forget()
                btn_toggle.configure(text="▼")
            else:
                self._expandidos.add(path)
                separador.pack(fill=tk.X, padx=12)
                panel.pack(fill=tk.X, padx=12, pady=(4, 10))
                self._llenar_panel(panel, info["transcripcion"])
                btn_toggle.configure(text="▲")
            self.contenedor.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        btn_toggle.bind("<Button-1>", _toggle)
        btn_toggle.bind("<Enter>", lambda e: btn_toggle.configure(fg=TEXT_PRIMARY))
        btn_toggle.bind("<Leave>", lambda e: btn_toggle.configure(fg=TEXT_ACCENT))

    def _llenar_panel(self, panel, texto):
        for w in panel.winfo_children():
            w.destroy()

        # Fila superior con botón copiar
        fila_top = tk.Frame(panel, bg="#0d1117")
        fila_top.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(fila_top, text="Transcripción",
                font=self.f["small"], bg="#0d1117",
                fg=TEXT_MUTED).pack(side=tk.LEFT)

        btn_copiar = tk.Label(fila_top, text="📋  Copiar",
                            font=self.f["small"],
                            bg="#2d333b", fg=TEXT_ACCENT,
                            padx=8, pady=3, cursor="hand2")
        btn_copiar.pack(side=tk.RIGHT)
        btn_copiar.bind("<Enter>", lambda e: btn_copiar.configure(bg="#388bfd", fg="white"))
        btn_copiar.bind("<Leave>", lambda e: btn_copiar.configure(bg="#2d333b", fg=TEXT_ACCENT))
        btn_copiar.bind("<Button-1>", lambda e: self._copiar(texto, btn_copiar))

        # Texto
        tk.Label(panel, text=texto,
                font=self.f["small"], bg="#0d1117",
                fg=TEXT_PRIMARY, anchor="w", justify=tk.LEFT,
                wraplength=600).pack(fill=tk.X, pady=(2, 8), padx=8)

    def _copiar(self, texto, btn):
        self.clipboard_clear()
        self.clipboard_append(texto)
        btn.configure(text="✅  Copiado", bg=ACCENT_GREEN, fg="white")
        self.after(2000, lambda: btn.configure(
            text="📋  Copiar", bg="#2d333b", fg=TEXT_ACCENT))

    # ─── Scroll ───────────────────────────────────────────────────────────────
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._win, width=event.width)

    def _scroll(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")