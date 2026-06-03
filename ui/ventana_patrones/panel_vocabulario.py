# ─── RadioScript · ui/ventana_patrones/panel_vocabulario.py ──────────────────
import tkinter as tk
from tkinter import messagebox
from db.conexion import Conexion
from config import (
    BG_DARK, BG_CARD, BG_ITEM, BG_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW,
    BORDER
)


class PanelVocabulario(tk.Frame):
    """Panel para gestionar el vocabulario médico y correcciones de Whisper."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self._datos        = []
        self._seleccion_id = None
        self._construir_ui()
        self._cargar()

    # ─── UI ───────────────────────────────────────────────────────────────────
    def _construir_ui(self):
        # ── Barra superior ──
        barra = tk.Frame(self, bg=BG_DARK)
        barra.pack(fill=tk.X, pady=(0, 8))

        tk.Label(barra, text="🔤  Vocabulario Médico",
                 font=("Helvetica", 12, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(side=tk.LEFT)

        tk.Label(barra,
                 text="Agrega términos y sus variantes incorrectas para corregir la transcripción antes de enviarla a la IA",
                 font=("Helvetica", 9),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=12)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 10))

        # ── Cuerpo: lista izquierda + formulario derecho ──
        cuerpo = tk.Frame(self, bg=BG_DARK)
        cuerpo.pack(fill=tk.BOTH, expand=True)

        # Lista
        frame_lista = tk.Frame(cuerpo, bg=BG_DARK, width=320)
        frame_lista.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        frame_lista.pack_propagate(False)

        # Búsqueda
        frame_busq = tk.Frame(frame_lista, bg=BG_DARK)
        frame_busq.pack(fill=tk.X, pady=(0, 6))
        self.var_busq = tk.StringVar()
        self.var_busq.trace("w", lambda *a: self._filtrar())
        ent_busq = tk.Entry(frame_busq, textvariable=self.var_busq,
                            font=("Helvetica", 10),
                            bg=BG_ITEM, fg=TEXT_PRIMARY,
                            insertbackground="white",
                            relief="flat")
        ent_busq.pack(fill=tk.X, ipady=5, padx=2)
        tk.Label(frame_busq, text="🔍 Buscar término",
                 font=("Helvetica", 8), bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w")

        # Listbox
        frame_lb = tk.Frame(frame_lista, bg=BG_DARK)
        frame_lb.pack(fill=tk.BOTH, expand=True)
        scroll = tk.Scrollbar(frame_lb)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(
            frame_lb,
            yscrollcommand=scroll.set,
            bg=BG_ITEM, fg=TEXT_PRIMARY,
            selectbackground=TEXT_ACCENT,
            selectforeground="white",
            font=("Helvetica", 10),
            bd=0, highlightthickness=0,
            activestyle="none",
            cursor="hand2"
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._al_seleccionar)

        # Botón nuevo
        self._boton(frame_lista, "➕  Nuevo Término", ACCENT_GREEN,
                    self._nuevo).pack(fill=tk.X, pady=(8, 0))

        # Separador
        tk.Frame(cuerpo, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Formulario derecho
        frame_form = tk.Frame(cuerpo, bg=BG_DARK)
        frame_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.lbl_form_titulo = tk.Label(
            frame_form, text="Selecciona un término para editar",
            font=("Helvetica", 11, "bold"),
            bg=BG_DARK, fg=TEXT_MUTED
        )
        self.lbl_form_titulo.pack(anchor="w", pady=(0, 12))

        # Término correcto
        tk.Label(frame_form, text="Término médico correcto (en mayúsculas):",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w")
        self.ent_termino = tk.Entry(frame_form,
                                    font=("Helvetica", 11),
                                    bg=BG_ITEM, fg=TEXT_PRIMARY,
                                    insertbackground="white",
                                    relief="flat")
        self.ent_termino.pack(fill=tk.X, ipady=6, pady=(2, 12))

        # Categoría
        tk.Label(frame_form, text="Categoría:",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w")
        self.var_cat = tk.StringVar(value="hallazgo")
        frame_cats = tk.Frame(frame_form, bg=BG_DARK)
        frame_cats.pack(anchor="w", pady=(2, 12))
        for cat in ("anatomía", "patología", "hallazgo", "técnica"):
            tk.Radiobutton(
                frame_cats, text=cat, variable=self.var_cat, value=cat,
                bg=BG_DARK, fg=TEXT_PRIMARY,
                selectcolor=BG_ITEM,
                activebackground=BG_DARK,
                font=("Helvetica", 10)
            ).pack(side=tk.LEFT, padx=(0, 12))

        # Variantes
        tk.Label(frame_form,
                 text="Variantes incorrectas de Whisper (separadas por coma):",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w")
        tk.Label(frame_form,
                 text="Ej: dextro escoliosis, dextrescoliosis, dextresco leosidorsal",
                 font=("Helvetica", 8),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        self.txt_variantes = tk.Text(frame_form, height=4,
                                      font=("Helvetica", 10),
                                      bg=BG_ITEM, fg=TEXT_PRIMARY,
                                      insertbackground="white",
                                      wrap=tk.WORD, relief="flat",
                                      padx=6, pady=6)
        self.txt_variantes.pack(fill=tk.X, pady=(0, 16))

        # Botones acción
        frame_btns = tk.Frame(frame_form, bg=BG_DARK)
        frame_btns.pack(anchor="w")
        self._boton(frame_btns, "💾  Guardar", ACCENT_GREEN,
                    self._guardar).pack(side=tk.LEFT, padx=(0, 8))
        self._boton(frame_btns, "🗑  Eliminar", ACCENT_RED,
                    self._eliminar).pack(side=tk.LEFT)

        self.lbl_estado = tk.Label(frame_form, text="",
                                   font=("Helvetica", 9),
                                   bg=BG_DARK, fg=ACCENT_GREEN)
        self.lbl_estado.pack(anchor="w", pady=(8, 0))

        # ── Ayuda inferior ──
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(10, 6))
        tk.Label(self,
                 text="💡  Cómo funciona: antes de enviar la transcripción a la IA, el sistema reemplaza automáticamente "
                      "cada variante incorrecta por el término correcto. Así la IA recibe texto médico limpio.",
                 font=("Helvetica", 9), bg=BG_DARK, fg=TEXT_MUTED,
                 wraplength=800, justify=tk.LEFT).pack(anchor="w", padx=4)

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
    def _cargar(self, filtro: str = ""):
        cur = Conexion.cursor()
        if filtro:
            cur.execute(
                "SELECT * FROM vocabulario WHERE termino LIKE %s OR variantes LIKE %s "
                "ORDER BY termino",
                (f"%{filtro}%", f"%{filtro}%")
            )
        else:
            cur.execute("SELECT * FROM vocabulario ORDER BY termino")
        self._datos = cur.fetchall()
        cur.close()

        self.listbox.delete(0, tk.END)
        for row in self._datos:
            cat = row.get("categoria", "")
            self.listbox.insert(tk.END, f"  {row['termino']}  [{cat}]")

    def _filtrar(self):
        self._cargar(filtro=self.var_busq.get().strip())

    def _al_seleccionar(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        row = self._datos[sel[0]]
        self._seleccion_id = row["id"]
        self.lbl_form_titulo.configure(
            text=f"Editando: {row['termino']}", fg=TEXT_ACCENT)
        self.ent_termino.delete(0, tk.END)
        self.ent_termino.insert(0, row["termino"])
        self.var_cat.set(row.get("categoria") or "hallazgo")
        self.txt_variantes.delete(1.0, tk.END)
        self.txt_variantes.insert(tk.END, row.get("variantes") or "")

    def _nuevo(self):
        self._seleccion_id = None
        self.lbl_form_titulo.configure(text="Nuevo término", fg=ACCENT_GREEN)
        self.ent_termino.delete(0, tk.END)
        self.var_cat.set("hallazgo")
        self.txt_variantes.delete(1.0, tk.END)
        self.ent_termino.focus_set()

    def _guardar(self):
        termino   = self.ent_termino.get().strip().upper()
        variantes = self.txt_variantes.get(1.0, tk.END).strip()
        categoria = self.var_cat.get()

        if not termino:
            messagebox.showwarning("Aviso", "El término no puede estar vacío.", parent=self)
            return

        cur = Conexion.cursor()
        if self._seleccion_id:
            cur.execute(
                "UPDATE vocabulario SET termino=%s, variantes=%s, categoria=%s WHERE id=%s",
                (termino, variantes, categoria, self._seleccion_id)
            )
        else:
            cur.execute(
                "INSERT INTO vocabulario (termino, variantes, categoria) VALUES (%s, %s, %s)",
                (termino, variantes, categoria)
            )
            self._seleccion_id = cur.lastrowid
        cur.close()
        self._cargar(filtro=self.var_busq.get().strip())
        self._flash(f"✅ '{termino}' guardado correctamente", ACCENT_GREEN)

    def _eliminar(self):
        if not self._seleccion_id:
            messagebox.showwarning("Aviso", "Selecciona un término primero.", parent=self)
            return
        termino = self.ent_termino.get().strip()
        if not messagebox.askyesno(
            "Eliminar",
            f"¿Eliminar el término '{termino}'?",
            parent=self
        ):
            return
        cur = Conexion.cursor()
        cur.execute("DELETE FROM vocabulario WHERE id=%s", (self._seleccion_id,))
        cur.close()
        self._seleccion_id = None
        self.lbl_form_titulo.configure(
            text="Selecciona un término para editar", fg=TEXT_MUTED)
        self.ent_termino.delete(0, tk.END)
        self.txt_variantes.delete(1.0, tk.END)
        self._cargar(filtro=self.var_busq.get().strip())
        self._flash(f"🗑 Término eliminado", ACCENT_RED)

    def _flash(self, texto, color):
        self.lbl_estado.configure(text=texto, fg=color)
        self.after(3000, lambda: self.lbl_estado.configure(text=""))