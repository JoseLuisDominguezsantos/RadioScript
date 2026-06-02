# ─── RadioScript · ui/ventana_patrones/ventana_principal.py ──────────────────
import tkinter as tk
from ui.ventana_patrones.panel_estudios import PanelEstudios
from ui.ventana_patrones.panel_hallazgos import PanelHallazgos
from config import BG_DARK, BG_CARD, BORDER, TEXT_PRIMARY, TEXT_MUTED


class VentanaPatrones(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️  Gestión de Patrones — RadioScript")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.minsize(900, 600)

        self.transient(parent)
        self._construir_ui()

        # Centrar sobre la ventana padre
        self.update_idletasks()
        w, h = 1100, 680
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x  = px + (pw // 2) - (w // 2)
        y  = py + (ph // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.after(100, self.grab_set)  # ← espera 100ms antes de grab
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
    def _cerrar(self):
        self.grab_release()
        self.destroy()

    def _construir_ui(self):
        # ── Encabezado ──
        header = tk.Frame(self, bg=BG_CARD, pady=12)
        header.pack(fill=tk.X)

        tk.Label(header,
                 text="⚙️  Gestión de Patrones",
                 font=("Helvetica", 15, "bold"),
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(side=tk.LEFT, padx=20)

        tk.Label(header,
                 text="Administra tipos de estudio, categorías y hallazgos radiológicos",
                 font=("Helvetica", 10),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Cuerpo ──
        cuerpo = tk.Frame(self, bg=BG_DARK)
        cuerpo.pack(fill=tk.BOTH, expand=True)

        self.panel_estudios = PanelEstudios(
            cuerpo,
            on_seleccionar=self._al_seleccionar_estudio
        )
        self.panel_estudios.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 6), pady=12)

        tk.Frame(cuerpo, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, pady=12)

        self.panel_hallazgos = PanelHallazgos(cuerpo)
        self.panel_hallazgos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                                  padx=(6, 12), pady=12)

    def _al_seleccionar_estudio(self, tipo_id, tipo_nombre):
        self.panel_hallazgos.cargar_estudio(tipo_id, tipo_nombre)