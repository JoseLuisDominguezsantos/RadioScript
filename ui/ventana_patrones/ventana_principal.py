# ─── RadioScript · ui/ventana_patrones/ventana_principal.py ──────────────────
import tkinter as tk
from tkinter import ttk
from ui.ventana_patrones.panel_estudios   import PanelEstudios
from ui.ventana_patrones.panel_hallazgos  import PanelHallazgos
from ui.ventana_patrones.panel_plantillas  import PanelPlantillas
from ui.ventana_patrones.panel_vocabulario    import PanelVocabulario
from ui.ventana_patrones.panel_entrenamiento import PanelEntrenamiento
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

        self.update_idletasks()
        w, h = 1100, 700
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x  = px + (pw // 2) - (w // 2)
        y  = py + (ph // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.after(100, self.grab_set)
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
                 text="Administra tipos de estudio, hallazgos y plantillas base para la IA",
                 font=("Helvetica", 10),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X)

        # ── Cuerpo con pestañas ──
        cuerpo = tk.Frame(self, bg=BG_DARK)
        cuerpo.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Panel izquierdo: tipos de estudio (siempre visible)
        self.panel_estudios = PanelEstudios(
            cuerpo,
            on_seleccionar=self._al_seleccionar_estudio
        )
        self.panel_estudios.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        tk.Frame(cuerpo, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Panel derecho con pestañas
        frame_der = tk.Frame(cuerpo, bg=BG_DARK)
        frame_der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        # Estilo de pestañas
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Radio.TNotebook",
                         background=BG_DARK,
                         borderwidth=0)
        style.configure("Radio.TNotebook.Tab",
                         background=BG_CARD,
                         foreground=TEXT_MUTED,
                         padding=[14, 6],
                         font=("Helvetica", 10, "bold"))
        style.map("Radio.TNotebook.Tab",
                  background=[("selected", BG_DARK)],
                  foreground=[("selected", TEXT_PRIMARY)])

        self.notebook = ttk.Notebook(frame_der, style="Radio.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Pestaña 1: Hallazgos
        self.panel_hallazgos = PanelHallazgos(self.notebook)
        self.notebook.add(self.panel_hallazgos, text="  🏷  Hallazgos  ")

        # Pestaña 2: Plantilla base
        self.panel_plantillas = PanelPlantillas(self.notebook)
        self.notebook.add(self.panel_plantillas, text="  📄  Plantilla Base  ")

        # Pestaña 3: Vocabulario
        self.panel_vocabulario = PanelVocabulario(self.notebook)
        self.notebook.add(self.panel_vocabulario, text="  🔤  Vocabulario  ")

        # Pestaña 4: Entrenamiento
        self.panel_entrenamiento = PanelEntrenamiento(self.notebook)
        self.notebook.add(self.panel_entrenamiento, text="  🧠  Entrenamiento  ")

    def _al_seleccionar_estudio(self, tipo_id, tipo_nombre):
        self.panel_hallazgos.cargar_estudio(tipo_id, tipo_nombre)
        # Sincronizar el selector de tipo en plantillas
        for t in self.panel_plantillas._tipos:
            if t["id"] == tipo_id:
                self.panel_plantillas.var_tipo.set(t["nombre"])
                self.panel_plantillas._tipo_sel_id = tipo_id
                self.panel_plantillas._cargar_plantilla()
                break