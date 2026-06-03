# ─── RadioScript · ui/ventana_patrones/panel_plantillas.py ──────────────────
import tkinter as tk
from tkinter import messagebox, scrolledtext
from db.conexion import Conexion
from config import (
    BG_DARK, BG_CARD, BG_ITEM, BG_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW,
    BORDER
)


class PanelPlantillas(tk.Frame):
    """Panel para crear y editar plantillas base por tipo de estudio."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self._tipos        = []
        self._plantilla_id = None   # plantilla actualmente cargada
        self._tipo_sel_id  = None
        self._construir_ui()
        self._cargar_tipos()

    # ─── UI ───────────────────────────────────────────────────────────────────
    def _construir_ui(self):
        # ── Fila superior: selector de tipo + botones ──
        fila_top = tk.Frame(self, bg=BG_DARK)
        fila_top.pack(fill=tk.X, pady=(0, 8))

        tk.Label(fila_top, text="Tipo de Estudio:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(side=tk.LEFT, padx=(0, 8))

        self.var_tipo = tk.StringVar(value="Selecciona un tipo...")
        self.om_tipo  = tk.OptionMenu(fila_top, self.var_tipo, "Cargando...")
        self.om_tipo.configure(bg=BG_CARD, fg=TEXT_PRIMARY,
                               font=("Helvetica", 10),
                               highlightthickness=0,
                               activebackground=TEXT_ACCENT,
                               relief="flat", width=28)
        self.om_tipo["menu"].configure(bg=BG_CARD, fg=TEXT_PRIMARY,
                                       activebackground=TEXT_ACCENT,
                                       activeforeground="white")
        self.om_tipo.pack(side=tk.LEFT)

        self._boton(fila_top, "🔍  Cargar", TEXT_ACCENT,
                    self._cargar_plantilla).pack(side=tk.LEFT, padx=(10, 0))

        self._boton(fila_top, "💾  Guardar", ACCENT_GREEN,
                    self._guardar).pack(side=tk.LEFT, padx=(6, 0))

        self._boton(fila_top, "🗑  Limpiar", ACCENT_RED,
                    self._confirmar_limpiar).pack(side=tk.LEFT, padx=(6, 0))

        self.lbl_estado = tk.Label(fila_top, text="",
                                   font=("Helvetica", 9),
                                   bg=BG_DARK, fg=ACCENT_GREEN)
        self.lbl_estado.pack(side=tk.LEFT, padx=12)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 10))

        # ── Nombre de la plantilla ──
        fila_nombre = tk.Frame(self, bg=BG_DARK)
        fila_nombre.pack(fill=tk.X, pady=(0, 8))
        tk.Label(fila_nombre, text="Nombre de la plantilla:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(side=tk.LEFT, padx=(0, 8))
        self.ent_nombre = tk.Entry(fila_nombre,
                                   font=("Helvetica", 10),
                                   bg=BG_ITEM, fg=TEXT_PRIMARY,
                                   insertbackground="white",
                                   relief="flat", width=40)
        self.ent_nombre.pack(side=tk.LEFT, ipady=4)

        # ── Cuerpo: tres columnas (técnica | hallazgos | conclusión) ──
        cuerpo = tk.Frame(self, bg=BG_DARK)
        cuerpo.pack(fill=tk.BOTH, expand=True)

        # Técnica
        col1 = tk.Frame(cuerpo, bg=BG_DARK)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 8))

        tk.Label(col1, text="TÉCNICA:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_ACCENT).pack(anchor="w", pady=(0, 4))
        self.txt_tecnica = tk.Text(col1, width=28, height=5,
                                    font=("Helvetica", 10),
                                    bg=BG_ITEM, fg=TEXT_PRIMARY,
                                    insertbackground="white",
                                    wrap=tk.WORD, relief="flat",
                                    padx=8, pady=6)
        self.txt_tecnica.pack(fill=tk.X)

        tk.Label(col1, text="Ej: Radiografía de Tórax PA.",
                 font=("Helvetica", 8),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Separador
        tk.Frame(cuerpo, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Hallazgos base
        col2 = tk.Frame(cuerpo, bg=BG_DARK)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(col2, text="HALLAZGOS BASE:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_ACCENT).pack(anchor="w", pady=(0, 4))

        scroll2 = tk.Scrollbar(col2)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_hallazgos = tk.Text(col2,
                                      font=("Helvetica", 10),
                                      bg=BG_ITEM, fg=TEXT_PRIMARY,
                                      insertbackground="white",
                                      wrap=tk.WORD, relief="flat",
                                      padx=8, pady=6,
                                      yscrollcommand=scroll2.set)
        self.txt_hallazgos.pack(fill=tk.BOTH, expand=True)
        scroll2.config(command=self.txt_hallazgos.yview)

        tk.Label(col2,
                 text="Escribe los hallazgos normales línea a línea.",
                 font=("Helvetica", 8),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Separador
        tk.Frame(cuerpo, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Conclusión base
        col3 = tk.Frame(cuerpo, bg=BG_DARK)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 0))

        tk.Label(col3, text="IMPRESIÓN DIAGNÓSTICA BASE:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_ACCENT).pack(anchor="w", pady=(0, 4))

        self.txt_conclusion = tk.Text(col3, width=32, height=8,
                                       font=("Helvetica", 10),
                                       bg=BG_ITEM, fg=TEXT_PRIMARY,
                                       insertbackground="white",
                                       wrap=tk.WORD, relief="flat",
                                       padx=8, pady=6)
        self.txt_conclusion.pack(fill=tk.BOTH, expand=True)

        tk.Label(col3,
                 text="Conclusión cuando el estudio es normal.",
                 font=("Helvetica", 8),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

    def _boton(self, parent, texto, color, comando):
        hover = {ACCENT_GREEN: "#5dd879", ACCENT_RED: "#ff6b6b",
                 TEXT_ACCENT: "#79b8ff"}.get(color, color)
        b = tk.Label(parent, text=texto, font=("Helvetica", 10, "bold"),
                     bg=color, fg="white", padx=10, pady=5, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>",    lambda e: b.configure(bg=hover))
        b.bind("<Leave>",    lambda e: b.configure(bg=color))
        return b

    # ─── Datos ────────────────────────────────────────────────────────────────
    def _cargar_tipos(self):
        cur = Conexion.cursor()
        cur.execute("SELECT id, nombre FROM tipos_estudio ORDER BY nombre")
        self._tipos = cur.fetchall()
        cur.close()

        menu = self.om_tipo["menu"]
        menu.delete(0, tk.END)
        for t in self._tipos:
            menu.add_command(
                label=t["nombre"],
                command=lambda nombre=t["nombre"]: self.var_tipo.set(nombre)
            )
        if self._tipos:
            self.var_tipo.set(self._tipos[0]["nombre"])

    def _tipo_id_seleccionado(self):
        nombre = self.var_tipo.get()
        for t in self._tipos:
            if t["nombre"] == nombre:
                return t["id"]
        return None

    def _cargar_plantilla(self):
        tipo_id = self._tipo_id_seleccionado()
        if not tipo_id:
            return

        self._tipo_sel_id = tipo_id
        cur = Conexion.cursor()
        cur.execute(
            "SELECT * FROM plantillas WHERE tipo_estudio_id = %s AND activo = 1 "
            "ORDER BY id DESC LIMIT 1",
            (tipo_id,)
        )
        plantilla = cur.fetchone()
        cur.close()

        # Limpiar campos
        self.ent_nombre.delete(0, tk.END)
        self.txt_tecnica.delete(1.0, tk.END)
        self.txt_hallazgos.delete(1.0, tk.END)
        self.txt_conclusion.delete(1.0, tk.END)

        if plantilla:
            self._plantilla_id = plantilla["id"]
            self.ent_nombre.insert(0, plantilla["nombre"] or "")
            self.txt_tecnica.insert(tk.END, plantilla["tecnica"] or "")
            self.txt_hallazgos.insert(tk.END, plantilla["hallazgos_base"] or "")
            self.txt_conclusion.insert(tk.END, plantilla["conclusion_base"] or "")
            self._flash("✅ Plantilla cargada", ACCENT_GREEN)
        else:
            self._plantilla_id = None
            tipo_nombre = self.var_tipo.get()
            self.ent_nombre.insert(0, f"{tipo_nombre} Normal")
            self._flash("⚠ Sin plantilla — completa los campos y guarda", ACCENT_YELLOW)

    def _guardar(self):
        tipo_id = self._tipo_id_seleccionado()
        if not tipo_id:
            messagebox.showwarning("Aviso", "Selecciona un tipo de estudio.", parent=self)
            return

        nombre     = self.ent_nombre.get().strip()
        tecnica    = self.txt_tecnica.get(1.0, tk.END).strip()
        hallazgos  = self.txt_hallazgos.get(1.0, tk.END).strip()
        conclusion = self.txt_conclusion.get(1.0, tk.END).strip()

        if not nombre:
            messagebox.showwarning("Aviso", "El nombre de la plantilla no puede estar vacío.", parent=self)
            return
        if not hallazgos:
            messagebox.showwarning("Aviso", "Los hallazgos base no pueden estar vacíos.", parent=self)
            return

        cur = Conexion.cursor()
        if self._plantilla_id:
            cur.execute(
                "UPDATE plantillas SET nombre=%s, tecnica=%s, hallazgos_base=%s, "
                "conclusion_base=%s WHERE id=%s",
                (nombre, tecnica, hallazgos, conclusion, self._plantilla_id)
            )
        else:
            cur.execute(
                "INSERT INTO plantillas (tipo_estudio_id, nombre, tecnica, "
                "hallazgos_base, conclusion_base, activo) VALUES (%s,%s,%s,%s,%s,1)",
                (tipo_id, nombre, tecnica, hallazgos, conclusion)
            )
            self._plantilla_id = cur.lastrowid
        cur.close()
        self._flash("✅ Plantilla guardada correctamente", ACCENT_GREEN)

    def _confirmar_limpiar(self):
        if not self._plantilla_id:
            self._limpiar_campos()
            return
        if messagebox.askyesno(
            "Eliminar plantilla",
            "¿Eliminar la plantilla de este tipo de estudio?\nEsta acción no se puede deshacer.",
            parent=self
        ):
            cur = Conexion.cursor()
            cur.execute("DELETE FROM plantillas WHERE id = %s", (self._plantilla_id,))
            cur.close()
            self._plantilla_id = None
            self._limpiar_campos()
            self._flash("🗑 Plantilla eliminada", ACCENT_RED)

    def _limpiar_campos(self):
        self.ent_nombre.delete(0, tk.END)
        self.txt_tecnica.delete(1.0, tk.END)
        self.txt_hallazgos.delete(1.0, tk.END)
        self.txt_conclusion.delete(1.0, tk.END)

    def _flash(self, texto, color):
        self.lbl_estado.configure(text=texto, fg=color)
        self.after(3000, lambda: self.lbl_estado.configure(text=""))