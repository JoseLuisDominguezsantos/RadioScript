# ─── RadioScript · ui/drop_zone.py ───────────────────────────────────────────
import tkinter as tk
from tkinterdnd2 import DND_FILES
from config import *


class DropZone(tk.Frame):
    """Zona de arrastre completa — toda el área acepta archivos."""

    def __init__(self, parent, on_archivos, on_abrir, fuentes, **kwargs):
        super().__init__(parent, bg=BG_CARD,
                         highlightthickness=2,
                         highlightbackground=BORDER, **kwargs)
        self.on_archivos = on_archivos
        self.on_abrir    = on_abrir
        self.f           = fuentes
        self._activo     = False
        self._flash_job  = None
        self._flash_idx  = 0

        self._build()
        self._registrar_dnd_recursivo(self)

    # ─── UI ──────────────────────────────────────────────────────────────────
    def _build(self):
        self._todos_widgets = []

        # Frame centrado con contenido
        self._inner = tk.Frame(self, bg=BG_CARD)
        self._inner.pack(expand=True, pady=22, padx=20)

        self.lbl_icono = tk.Label(self._inner, text=ICONO_SUBIR,
                                  font=self.f["icon"], bg=BG_CARD, fg=TEXT_MUTED)
        self.lbl_icono.pack()

        self.lbl_texto = tk.Label(self._inner,
                                  text="Arrastra los audios aquí",
                                  font=self.f["label"], bg=BG_CARD, fg=TEXT_MUTED)
        self.lbl_texto.pack(pady=(4, 2))

        self.lbl_formato = tk.Label(self._inner,
                                    text="OGG · MP3 · WAV · M4A · OPUS · FLAC",
                                    font=self.f["small"], bg=BG_CARD, fg=TEXT_MUTED)
        self.lbl_formato.pack()

        tk.Frame(self._inner, bg=BORDER, height=1, width=200).pack(pady=12)

        self.btn_sel = tk.Label(self._inner,
                                text=f"{ICONO_CARPETA}  Seleccionar Archivos",
                                font=self.f["label"], bg=ACCENT_BLUE, fg="white",
                                padx=16, pady=8, cursor="hand2")
        self.btn_sel.pack()
        self.btn_sel.bind("<Button-1>", lambda e: self.on_abrir())
        self.btn_sel.bind("<Enter>",    lambda e: self.btn_sel.configure(bg="#4a9eff"))
        self.btn_sel.bind("<Leave>",    lambda e: self.btn_sel.configure(bg=ACCENT_BLUE))

        self.configure(height=160)

    # ─── DND recursivo ───────────────────────────────────────────────────────
    def _registrar_dnd_recursivo(self, widget):
        """Registra drag & drop en el widget y todos sus hijos recursivamente."""
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            widget.dnd_bind("<<DragLeave>>", self._on_drag_leave)
            widget.dnd_bind("<<Drop>>",      self._on_drop)
        except Exception:
            pass
        for hijo in widget.winfo_children():
            self._registrar_dnd_recursivo(hijo)

    # ─── Eventos DND ─────────────────────────────────────────────────────────
    def _on_drag_enter(self, event):
        if not self._activo:
            self._activo = True
            self._mostrar_activo()

    def _on_drag_leave(self, event):
        # Solo desactivar si el mouse salió realmente del área total
        try:
            x, y   = self.winfo_pointerxy()
            rx, ry = self.winfo_rootx(), self.winfo_rooty()
            rw, rh = self.winfo_width(), self.winfo_height()
            if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
                self._activo = False
                self._reset()
        except Exception:
            self._activo = False
            self._reset()

    def _on_drop(self, event):
        self._activo = False
        paths = self.tk.splitlist(event.data)
        self._flash_exito()
        self.after(600, self._reset)
        self.on_archivos(list(paths))

    # ─── Estados visuales ────────────────────────────────────────────────────
    def _aplicar_color(self, bg, fg_icono, fg_texto, fg_formato,
                       icono, texto, borde):
        self.configure(bg=bg, highlightbackground=borde)
        self._inner.configure(bg=bg)
        self.lbl_icono.configure(bg=bg, fg=fg_icono, text=icono)
        self.lbl_texto.configure(bg=bg, fg=fg_texto, text=texto)
        self.lbl_formato.configure(bg=bg, fg=fg_formato)

    def _mostrar_activo(self):
        BG_A = "#0d1f3c"
        self._aplicar_color(
            bg=BG_A,
            fg_icono=ACCENT_BLUE,
            fg_texto=TEXT_PRIMARY,
            fg_formato=TEXT_ACCENT,
            icono="⬇",
            texto="Suelta los archivos aquí",
            borde=ACCENT_BLUE
        )
        self.btn_sel.configure(bg=BG_A, fg=TEXT_MUTED)
        self._pulsar_borde()

    def _flash_exito(self):
        BG_G = "#0d2b1a"
        self._pulsar_borde(detener=True)
        self._aplicar_color(
            bg=BG_G,
            fg_icono=ACCENT_GREEN,
            fg_texto=ACCENT_GREEN,
            fg_formato=ACCENT_GREEN,
            icono=ICONO_OK,
            texto="¡Archivos recibidos!",
            borde=ACCENT_GREEN
        )
        self.btn_sel.configure(bg=BG_G, fg=ACCENT_GREEN)

    def _reset(self):
        self._pulsar_borde(detener=True)
        self._aplicar_color(
            bg=BG_CARD,
            fg_icono=TEXT_MUTED,
            fg_texto=TEXT_MUTED,
            fg_formato=TEXT_MUTED,
            icono=ICONO_SUBIR,
            texto="Arrastra los audios aquí",
            borde=BORDER
        )
        self.btn_sel.configure(bg=ACCENT_BLUE, fg="white")

    # ─── Animación pulso borde ────────────────────────────────────────────────
    def _pulsar_borde(self, detener=False):
        if self._flash_job:
            self.after_cancel(self._flash_job)
            self._flash_job  = None
            self._flash_idx  = 0
        if detener:
            return

        colores = ["#388bfd", "#1a4a8a", "#388bfd", "#1a4a8a"]

        def _paso():
            if not self._activo:
                return
            self.configure(highlightbackground=colores[self._flash_idx % len(colores)])
            self._flash_idx += 1
            self._flash_job = self.after(350, _paso)

        _paso()