# ─── RadioScript · ui/ventana_patrones/panel_hallazgos.py ────────────────────
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from db.conexion import Conexion
from config import (
    BG_DARK, BG_CARD, BG_ITEM,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_RED, BORDER
)

BG_CATEGORIA = "#12121f"


class PanelHallazgos(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.tipo_id     = None
        self.tipo_nombre = None
        self._construir_ui()
        self._mostrar_placeholder()

    def _construir_ui(self):
        self.header = tk.Frame(self, bg=BG_DARK)
        self.header.pack(fill=tk.X, pady=(0, 6))

        self.lbl_titulo = tk.Label(
            self.header,
            text="← Selecciona un tipo de estudio",
            font=("Helvetica", 12, "bold"),
            bg=BG_DARK, fg=TEXT_MUTED
        )
        self.lbl_titulo.pack(side=tk.LEFT)

        frame_btns = tk.Frame(self.header, bg=BG_DARK)
        frame_btns.pack(side=tk.RIGHT)

        self._btn_accion(frame_btns, "➕ Nueva Categoría", ACCENT_GREEN,
                         self.nueva_categoria).pack(side=tk.LEFT, padx=4)
        self._btn_accion(frame_btns, "➕ Nuevo Hallazgo", TEXT_ACCENT,
                         self.nuevo_hallazgo).pack(side=tk.LEFT, padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 8))

        contenedor = tk.Frame(self, bg=BG_DARK)
        contenedor.pack(fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(contenedor)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(
            contenedor, bg=BG_DARK, bd=0,
            highlightthickness=0,
            yscrollcommand=scroll.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.canvas.yview)

        self.frame_scroll = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame_scroll, anchor="nw"
        )

        self.frame_scroll.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll( 1, "units"))

    def _btn_accion(self, parent, texto, color, comando):
        hover = {"#3fb950": "#5dd879", "#f85149": "#ff6b6b", "#58a6ff": "#79b8ff"}.get(color, color)
        b = tk.Label(parent, text=texto, font=("Helvetica", 10, "bold"),
                     bg=color, fg="white", padx=10, pady=5, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>",    lambda e: b.configure(bg=hover))
        b.bind("<Leave>",    lambda e: b.configure(bg=color))
        return b

    def _mostrar_placeholder(self):
        for w in self.frame_scroll.winfo_children():
            w.destroy()
        tk.Label(
            self.frame_scroll,
            text="Selecciona un tipo de estudio\npara ver sus hallazgos",
            font=("Helvetica", 12), bg=BG_DARK, fg=TEXT_MUTED,
            justify=tk.CENTER
        ).pack(pady=80)

    def cargar_estudio(self, tipo_id, tipo_nombre):
        self.tipo_id     = tipo_id
        self.tipo_nombre = tipo_nombre
        self.lbl_titulo.configure(text=f"📋  {tipo_nombre}", fg=TEXT_PRIMARY)
        self.refrescar()

    def refrescar(self):
        for w in self.frame_scroll.winfo_children():
            w.destroy()

        categorias = self._obtener_categorias()

        if not categorias:
            tk.Label(
                self.frame_scroll,
                text="Sin categorías todavía.\nUsa '➕ Nueva Categoría' para comenzar.",
                font=("Helvetica", 11), bg=BG_DARK, fg=TEXT_MUTED,
                justify=tk.CENTER
            ).pack(pady=60)
            return

        for cat in categorias:
            self._renderizar_categoria(cat)

    def _renderizar_categoria(self, categoria):
        frame_cat = tk.Frame(self.frame_scroll, bg=BG_CATEGORIA, pady=6)
        frame_cat.pack(fill=tk.X, pady=(8, 0), padx=4)

        tk.Label(frame_cat, text=f"  🏷  {categoria}",
                 font=("Helvetica", 11, "bold"),
                 bg=BG_CATEGORIA, fg=TEXT_ACCENT).pack(side=tk.LEFT, padx=8)

        self._mini_btn(frame_cat, "✏️", TEXT_ACCENT,
                       lambda c=categoria: self.renombrar_categoria(c)).pack(side=tk.RIGHT, padx=4)
        self._mini_btn(frame_cat, "🗑", ACCENT_RED,
                       lambda c=categoria: self.eliminar_categoria(c)).pack(side=tk.RIGHT, padx=4)

        frame_items = tk.Frame(self.frame_scroll, bg=BG_ITEM)
        frame_items.pack(fill=tk.X, padx=4, pady=(0, 4))

        hallazgos = self._obtener_hallazgos(categoria)
        # Filtrar filas vacías (marcador de categoría sin hallazgos)
        validos = [h for h in hallazgos if h["frase"].strip()]

        if not validos:
            tk.Label(frame_items,
                     text="  Sin hallazgos en esta categoría.",
                     font=("Helvetica", 9), bg=BG_ITEM, fg=TEXT_MUTED
                     ).pack(anchor="w", padx=12, pady=4)
        else:
            for h in validos:
                self._renderizar_hallazgo(frame_items, h)

    def _renderizar_hallazgo(self, parent, hallazgo):
        row = tk.Frame(parent, bg=BG_ITEM, pady=4)
        row.pack(fill=tk.X, padx=8)

        tk.Label(row, text=hallazgo["frase"],
                 font=("Helvetica", 10), bg=BG_ITEM, fg=TEXT_PRIMARY,
                 anchor="w", justify=tk.LEFT, wraplength=680
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 8))

        self._mini_btn(row, "✏️", TEXT_ACCENT,
                       lambda h=hallazgo: self.editar_hallazgo(h)).pack(side=tk.RIGHT, padx=2)
        self._mini_btn(row, "🗑", ACCENT_RED,
                       lambda h=hallazgo: self.eliminar_hallazgo(h)).pack(side=tk.RIGHT, padx=2)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=8)

    def _mini_btn(self, parent, texto, color, comando):
        hover = {"#3fb950": "#5dd879", "#f85149": "#ff6b6b", "#58a6ff": "#79b8ff"}.get(color, color)
        b = tk.Label(parent, text=texto, font=("Helvetica", 10),
                     bg=BG_CATEGORIA, fg=color, padx=6, pady=2, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>",    lambda e: b.configure(fg=hover))
        b.bind("<Leave>",    lambda e: b.configure(fg=color))
        return b

    # ── Consultas ─────────────────────────────────────────────────────────────
    def _obtener_categorias(self):
        """Devuelve todas las categorías incluyendo las recién creadas."""
        cur = Conexion.cursor()
        cur.execute(
            "SELECT DISTINCT categoria FROM hallazgos "
            "WHERE tipo_estudio_id = %s ORDER BY categoria",
            (self.tipo_id,)
        )
        resultado = [row["categoria"] for row in cur.fetchall()]
        cur.close()
        return resultado

    def _obtener_hallazgos(self, categoria):
        cur = Conexion.cursor()
        cur.execute(
            "SELECT * FROM hallazgos WHERE tipo_estudio_id = %s "
            "AND categoria = %s ORDER BY frase",
            (self.tipo_id, categoria)
        )
        resultado = cur.fetchall()
        cur.close()
        return resultado

    # ── CRUD Categorías ───────────────────────────────────────────────────────
    def nueva_categoria(self):
        if not self.tipo_id:
            messagebox.showwarning("Aviso", "Selecciona un tipo de estudio primero.", parent=self)
            return
        nombre = simpledialog.askstring(
            "Nueva Categoría",
            "Nombre de la categoría (ej: AORTA, PULMONES):",
            parent=self
        )
        if not nombre or not nombre.strip():
            return
        cur = Conexion.cursor()
        cur.execute(
            "INSERT INTO hallazgos (tipo_estudio_id, categoria, frase) VALUES (%s, %s, %s)",
            (self.tipo_id, nombre.strip().upper(), "")
        )
        cur.close()
        messagebox.showinfo(
            "Categoría creada",
            f"Categoría '{nombre.strip().upper()}' creada.\n\nAhora usa '➕ Nuevo Hallazgo' para agregar frases.",
            parent=self
        )
        self.refrescar()

    def renombrar_categoria(self, categoria):
        nuevo = simpledialog.askstring(
            "Renombrar Categoría",
            f"Nuevo nombre para '{categoria}':",
            initialvalue=categoria,
            parent=self
        )
        if not nuevo or not nuevo.strip() or nuevo.strip().upper() == categoria:
            return
        cur = Conexion.cursor()
        cur.execute(
            "UPDATE hallazgos SET categoria = %s "
            "WHERE tipo_estudio_id = %s AND categoria = %s",
            (nuevo.strip().upper(), self.tipo_id, categoria)
        )
        cur.close()
        self.refrescar()

    def eliminar_categoria(self, categoria):
        if not messagebox.askyesno(
            "Eliminar Categoría",
            f"¿Eliminar '{categoria}' y todos sus hallazgos?\nEsta acción no se puede deshacer.",
            parent=self
        ):
            return
        cur = Conexion.cursor()
        cur.execute(
            "DELETE FROM hallazgos WHERE tipo_estudio_id = %s AND categoria = %s",
            (self.tipo_id, categoria)
        )
        cur.close()
        self.refrescar()

    # ── CRUD Hallazgos ────────────────────────────────────────────────────────
    def nuevo_hallazgo(self):
        if not self.tipo_id:
            messagebox.showwarning("Aviso", "Selecciona un tipo de estudio primero.", parent=self)
            return
        categorias = self._obtener_categorias()
        if not categorias:
            messagebox.showwarning("Aviso", "Crea al menos una categoría primero.", parent=self)
            return
        DialogoHallazgo(
            self,
            categorias=categorias,
            on_guardar=self._guardar_nuevo_hallazgo
        )

    def _guardar_nuevo_hallazgo(self, categoria, frase):
        cur = Conexion.cursor()
        cur.execute(
            "INSERT INTO hallazgos (tipo_estudio_id, categoria, frase) VALUES (%s, %s, %s)",
            (self.tipo_id, categoria, frase.strip())
        )
        cur.close()
        self.refrescar()

    def editar_hallazgo(self, hallazgo):
        categorias = self._obtener_categorias()
        DialogoHallazgo(
            self,
            categorias=categorias,
            on_guardar=lambda cat, frase: self._actualizar_hallazgo(hallazgo["id"], cat, frase),
            categoria_inicial=hallazgo["categoria"],
            frase_inicial=hallazgo["frase"]
        )

    def _actualizar_hallazgo(self, hallazgo_id, categoria, frase):
        cur = Conexion.cursor()
        cur.execute(
            "UPDATE hallazgos SET categoria = %s, frase = %s WHERE id = %s",
            (categoria, frase.strip(), hallazgo_id)
        )
        cur.close()
        self.refrescar()

    def eliminar_hallazgo(self, hallazgo):
        texto = hallazgo["frase"][:80] + ("..." if len(hallazgo["frase"]) > 80 else "")
        if not messagebox.askyesno(
            "Eliminar Hallazgo",
            f"¿Eliminar este hallazgo?\n\n{texto}",
            parent=self
        ):
            return
        cur = Conexion.cursor()
        cur.execute("DELETE FROM hallazgos WHERE id = %s", (hallazgo["id"],))
        cur.close()
        self.refrescar()


# ── Diálogo agregar / editar hallazgo ─────────────────────────────────────────
class DialogoHallazgo(tk.Toplevel):
    def __init__(self, parent, categorias, on_guardar,
                categoria_inicial=None, frase_inicial=""):
        super().__init__(parent)
        self.title("Agregar / Editar Hallazgo")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.transient(parent)
        self.on_guardar = on_guardar
        self.categorias = categorias

        self._construir(categoria_inicial or categorias[0], frase_inicial)

        # Centrar sobre el padre
        self.update_idletasks()
        w, h = 500, 290
        x = parent.winfo_rootx() + (parent.winfo_width()  // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.after(100, self.grab_set)  # ← espera que sea visible
        self.bind("<Escape>", lambda e: self.destroy())

    def _construir(self, categoria_inicial, frase_inicial):
        tk.Label(self, text="Categoría:", font=("Helvetica", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(16, 2))

        self.var_cat = tk.StringVar(value=categoria_inicial)
        om = tk.OptionMenu(self, self.var_cat, *self.categorias)
        om.configure(bg=BG_CARD, fg=TEXT_PRIMARY, font=("Helvetica", 10),
                     highlightthickness=0, activebackground=TEXT_ACCENT,
                     relief="flat")
        om["menu"].configure(bg=BG_CARD, fg=TEXT_PRIMARY,
                             activebackground=TEXT_ACCENT, activeforeground="white")
        om.pack(fill=tk.X, padx=16, pady=(0, 4))

        tk.Label(self, text="Frase del hallazgo:", font=("Helvetica", 10, "bold"),
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(8, 2))

        self.txt = scrolledtext.ScrolledText(
            self, height=4, font=("Helvetica", 10),
            bg=BG_ITEM, fg=TEXT_PRIMARY,
            insertbackground="white", wrap=tk.WORD
        )
        self.txt.pack(fill=tk.X, padx=16)
        if frase_inicial:
            self.txt.insert(tk.END, frase_inicial)
        self.txt.focus_set()

        frame_btns = tk.Frame(self, bg=BG_CARD)
        frame_btns.pack(fill=tk.X, padx=16, pady=12)

        tk.Button(
            frame_btns, text="💾  Guardar",
            font=("Helvetica", 10, "bold"),
            bg=ACCENT_GREEN, fg="white", bd=0,
            padx=14, pady=6, cursor="hand2",
            command=self._guardar
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            frame_btns, text="Cancelar",
            font=("Helvetica", 10),
            bg=BG_ITEM, fg=TEXT_MUTED, bd=0,
            padx=14, pady=6, cursor="hand2",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=4)

    def _guardar(self):
        frase = self.txt.get(1.0, tk.END).strip()
        if not frase:
            messagebox.showwarning("Aviso", "La frase no puede estar vacía.", parent=self)
            return
        self.on_guardar(self.var_cat.get(), frase)
        self.destroy()