# ─── RadioScript · ui/ventana_patrones/panel_estudios.py ─────────────────────
import tkinter as tk
from tkinter import messagebox, simpledialog
from db.conexion import Conexion
from config import (
    BG_DARK, BG_CARD, BG_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_RED, BORDER
)


class PanelEstudios(tk.Frame):
    def __init__(self, parent, on_seleccionar):
        super().__init__(parent, bg=BG_CARD, width=220)
        self.pack_propagate(False)
        self.on_seleccionar  = on_seleccionar
        self.seleccionado_id = None
        self._datos          = []
        self._construir_ui()
        self.cargar()

    def _construir_ui(self):
        header = tk.Frame(self, bg=BG_CARD, pady=10)
        header.pack(fill=tk.X, padx=10)

        tk.Label(header, text="📋  Tipos de Estudio",
                 font=("Helvetica", 11, "bold"),
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor="w")

        tk.Label(header, text="Selecciona un estudio",
                 font=("Helvetica", 9),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, padx=10)

        contenedor = tk.Frame(self, bg=BG_CARD)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        scroll = tk.Scrollbar(contenedor, bg=BG_CARD)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.lista = tk.Listbox(
            contenedor,
            yscrollcommand=scroll.set,
            bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=TEXT_ACCENT,
            selectforeground="#ffffff",
            font=("Helvetica", 11),
            bd=0, highlightthickness=0,
            activestyle="none",
            cursor="hand2"
        )
        self.lista.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.lista.yview)
        self.lista.bind("<<ListboxSelect>>", self._al_seleccionar)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, padx=10)

        frame_btns = tk.Frame(self, bg=BG_CARD, pady=8)
        frame_btns.pack(fill=tk.X, padx=8)

        self._btn(frame_btns, "➕  Agregar",  ACCENT_GREEN, self.agregar ).pack(fill=tk.X, pady=2)
        self._btn(frame_btns, "✏️   Editar",   TEXT_ACCENT,  self.editar  ).pack(fill=tk.X, pady=2)
        self._btn(frame_btns, "🗑   Eliminar", ACCENT_RED,   self.eliminar).pack(fill=tk.X, pady=2)

    def _btn(self, parent, texto, color, comando):
        hover = {"#3fb950": "#5dd879", "#f85149": "#ff6b6b", "#58a6ff": "#79b8ff"}.get(color, color)
        b = tk.Label(parent, text=texto, font=("Helvetica", 10, "bold"),
                     bg=color, fg="white", pady=6, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>",    lambda e: b.configure(bg=hover))
        b.bind("<Leave>",    lambda e: b.configure(bg=color))
        return b

    def cargar(self):
        self.lista.delete(0, tk.END)
        cur = Conexion.cursor()
        cur.execute("SELECT id, nombre FROM tipos_estudio ORDER BY nombre")
        self._datos = cur.fetchall()
        cur.close()
        for t in self._datos:
            self.lista.insert(tk.END, f"  {t['nombre']}")

    def _al_seleccionar(self, event=None):
        sel = self.lista.curselection()
        if not sel:
            return
        tipo = self._datos[sel[0]]
        self.seleccionado_id = tipo["id"]
        self.on_seleccionar(tipo["id"], tipo["nombre"])

    def agregar(self):
        nombre = simpledialog.askstring(
            "Nuevo Tipo de Estudio",
            "Nombre del tipo de estudio:",
            parent=self
        )
        if not nombre or not nombre.strip():
            return
        cur = Conexion.cursor()
        cur.execute("INSERT INTO tipos_estudio (nombre) VALUES (%s)",
                    (nombre.strip().upper(),))
        cur.close()
        self.cargar()

    def editar(self):
        if not self.seleccionado_id:
            messagebox.showwarning("Aviso", "Selecciona un tipo de estudio primero.", parent=self)
            return
        tipo = next((t for t in self._datos if t["id"] == self.seleccionado_id), None)
        if not tipo:
            return
        nuevo = simpledialog.askstring("Editar", "Nuevo nombre:",
                                       initialvalue=tipo["nombre"], parent=self)
        if not nuevo or not nuevo.strip():
            return
        cur = Conexion.cursor()
        cur.execute("UPDATE tipos_estudio SET nombre = %s WHERE id = %s",
                    (nuevo.strip().upper(), self.seleccionado_id))
        cur.close()
        self.cargar()

    def eliminar(self):
        if not self.seleccionado_id:
            messagebox.showwarning("Aviso", "Selecciona un tipo de estudio primero.", parent=self)
            return
        tipo = next((t for t in self._datos if t["id"] == self.seleccionado_id), None)
        if not tipo:
            return
        if not messagebox.askyesno(
            "Eliminar",
            f"¿Eliminar '{tipo['nombre']}' y todos sus hallazgos?\nEsta acción no se puede deshacer.",
            parent=self
        ):
            return
        cur = Conexion.cursor()
        cur.execute("DELETE FROM hallazgos WHERE tipo_estudio_id = %s", (self.seleccionado_id,))
        cur.execute("DELETE FROM tipos_estudio WHERE id = %s", (self.seleccionado_id,))
        cur.close()
        self.seleccionado_id = None
        self.cargar()