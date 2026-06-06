# ─── RadioScript · ui/ventana_patrones/panel_entrenamiento.py ────────────────
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import os
from db.conexion import Conexion
from ui.procesador import contar_ejemplos, exportar_datos_entrenamiento, crear_modelfile
from config import (
    BG_DARK, BG_CARD, BG_ITEM, BG_HOVER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW, ACCENT_BLUE,
    BORDER
)

MINIMO_EJEMPLOS = 20   # mínimo recomendado para fine-tuning


class PanelEntrenamiento(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self._construir_ui()
        self._actualizar_stats()

    def _construir_ui(self):
        # ── Título ──
        tk.Label(self, text="🧠  Entrenamiento de la IA",
                 font=("Helvetica", 13, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 4))
        tk.Label(self,
                 text="Cuantos más reportes corrijas y guardes, mejor aprende la IA.",
                 font=("Helvetica", 9), bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w")
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=10)

        # ── Stats ──
        frame_stats = tk.Frame(self, bg=BG_CARD)
        frame_stats.pack(fill=tk.X, pady=(0, 16))

        self._stat("Total de ejemplos guardados", "0",  "total",      frame_stats)
        self._stat("Ejemplos con correcciones",   "0",  "alta",       frame_stats)
        self._stat("Modelo activo",               "—",  "modelo",     frame_stats)

        # ── Cómo funciona ──
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 12))
        tk.Label(self, text="¿Cómo aprende la IA?",
                 font=("Helvetica", 11, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 6))

        pasos = [
            ("1", "Procesas un audio → la IA genera un borrador",       ACCENT_BLUE),
            ("2", "Revisas el informe y corriges lo que está mal",       ACCENT_YELLOW),
            ("3", "Guardas el reporte → se registra el par original/corregido", ACCENT_GREEN),
            ("4", "El próximo audio recibe esos ejemplos como referencia",ACCENT_GREEN),
            ("5", "Con 20+ ejemplos puedes crear un modelo personalizado", TEXT_ACCENT),
        ]
        for num, texto, color in pasos:
            fila = tk.Frame(self, bg=BG_DARK)
            fila.pack(fill=tk.X, pady=2)
            tk.Label(fila, text=f" {num} ", font=("Helvetica", 9, "bold"),
                     bg=color, fg="white", padx=4).pack(side=tk.LEFT)
            tk.Label(fila, text=f"  {texto}",
                     font=("Helvetica", 9), bg=BG_DARK, fg=TEXT_MUTED).pack(side=tk.LEFT)

        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=12)

        # ── Fine-tuning ──
        tk.Label(self, text="Fine-Tuning — Modelo Personalizado",
                 font=("Helvetica", 11, "bold"),
                 bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 4))

        self.lbl_ft_info = tk.Label(self,
                 text="Acumula al menos 20 ejemplos corregidos para crear tu modelo.",
                 font=("Helvetica", 9), bg=BG_DARK, fg=TEXT_MUTED, wraplength=700,
                 justify=tk.LEFT)
        self.lbl_ft_info.pack(anchor="w", pady=(0, 12))

        frame_btns = tk.Frame(self, bg=BG_DARK)
        frame_btns.pack(anchor="w")

        self.btn_entrenar = self._boton(
            frame_btns, "🚀  Crear Modelo Personalizado",
            ACCENT_BLUE, self._iniciar_finetuning)
        self.btn_entrenar.pack(side=tk.LEFT, padx=(0, 10))

        self._boton(frame_btns, "🔄  Actualizar Stats",
                    BG_ITEM, self._actualizar_stats).pack(side=tk.LEFT)

        # Log de salida
        tk.Frame(self, bg=BORDER, height=1).pack(fill=tk.X, pady=(12, 6))
        tk.Label(self, text="Log:",
                 font=("Helvetica", 9, "bold"),
                 bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w")

        frame_log = tk.Frame(self, bg=BG_ITEM)
        frame_log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        scroll = tk.Scrollbar(frame_log)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_log = tk.Text(frame_log, height=8,
                               font=("Courier", 9),
                               bg="#0d1117", fg=TEXT_PRIMARY,
                               insertbackground="white",
                               relief="flat", state=tk.DISABLED,
                               yscrollcommand=scroll.set)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        scroll.config(command=self.txt_log.yview)

    def _stat(self, etiqueta, valor_inicial, key, parent):
        fila = tk.Frame(parent, bg=BG_CARD, pady=10)
        fila.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
        lbl_val = tk.Label(fila, text=valor_inicial,
                           font=("Helvetica", 22, "bold"),
                           bg=BG_CARD, fg=TEXT_ACCENT)
        lbl_val.pack()
        tk.Label(fila, text=etiqueta,
                 font=("Helvetica", 8), bg=BG_CARD, fg=TEXT_MUTED).pack()
        setattr(self, f"lbl_stat_{key}", lbl_val)

    def _boton(self, parent, texto, color, comando):
        hover = {ACCENT_GREEN: "#5dd879", ACCENT_RED: "#ff6b6b",
                 ACCENT_BLUE: "#4a9eff", BG_ITEM: BG_HOVER,
                 TEXT_ACCENT: "#79b8ff"}.get(color, color)
        b = tk.Label(parent, text=texto, font=("Helvetica", 10, "bold"),
                     bg=color, fg="white" if color != BG_ITEM else TEXT_MUTED,
                     padx=12, pady=6, cursor="hand2")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>",    lambda e: b.configure(bg=hover))
        b.bind("<Leave>",    lambda e: b.configure(bg=color))
        return b

    # ─── Stats ────────────────────────────────────────────────────────────────
    def _actualizar_stats(self):
        stats = contar_ejemplos()
        self.lbl_stat_total.configure(text=str(stats["total"]))
        self.lbl_stat_alta.configure(text=str(stats["alta_calidad"]))

        # Detectar modelo activo
        try:
            import urllib.request, json
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                modelos = [m["name"] for m in data.get("models", [])]
                if any("radioscript" in m for m in modelos):
                    self.lbl_stat_modelo.configure(
                        text="radioscript ✅", fg=ACCENT_GREEN)
                else:
                    self.lbl_stat_modelo.configure(
                        text="llama3.1:8b", fg=TEXT_ACCENT)
        except Exception:
            self.lbl_stat_modelo.configure(text="sin conexión", fg=ACCENT_RED)

        # Actualizar estado del botón
        suficientes = stats["alta_calidad"] >= MINIMO_EJEMPLOS
        if suficientes:
            self.btn_entrenar.configure(bg=ACCENT_BLUE, fg="white", cursor="hand2")
            self.lbl_ft_info.configure(
                text=f"✅ Tienes {stats['alta_calidad']} ejemplos corregidos — listo para crear el modelo.",
                fg=ACCENT_GREEN)
        else:
            faltan = MINIMO_EJEMPLOS - stats["alta_calidad"]
            self.btn_entrenar.configure(bg="#2d333b", fg=TEXT_MUTED, cursor="arrow")
            self.lbl_ft_info.configure(
                text=f"⏳ Faltan {faltan} ejemplos corregidos para habilitar el fine-tuning "
                     f"(tienes {stats['alta_calidad']} de {MINIMO_EJEMPLOS} necesarios).",
                fg=ACCENT_YELLOW)

    # ─── Fine-tuning ──────────────────────────────────────────────────────────
    def _iniciar_finetuning(self):
        stats = contar_ejemplos()
        if stats["alta_calidad"] < MINIMO_EJEMPLOS:
            messagebox.showwarning("Insuficiente",
                f"Necesitas al menos {MINIMO_EJEMPLOS} ejemplos corregidos.\n"
                f"Actualmente tienes {stats['alta_calidad']}.\n\n"
                "Sigue corrigiendo y guardando reportes.", parent=self)
            return

        if not messagebox.askyesno("Crear Modelo",
            f"Se creará el modelo 'radioscript' con {stats['alta_calidad']} ejemplos.\n\n"
            "Este proceso puede tardar varios minutos.\n¿Continuar?", parent=self):
            return

        self.btn_entrenar.configure(bg="#2d333b", fg=TEXT_MUTED,
                                    cursor="arrow", text="⏳ Entrenando...")
        threading.Thread(target=self._worker_finetuning, daemon=True).start()

    def _worker_finetuning(self):
        try:
            carpeta = os.path.join(os.path.expanduser("~"), ".radioscript")
            os.makedirs(carpeta, exist_ok=True)
            ruta_jsonl     = os.path.join(carpeta, "datos.jsonl")
            ruta_modelfile = os.path.join(carpeta, "Modelfile")

            self._log("📦 Exportando datos de entrenamiento...")
            n = exportar_datos_entrenamiento(ruta_jsonl)
            self._log(f"   → {n} ejemplos exportados a {ruta_jsonl}")

            self._log("📝 Generando Modelfile...")
            crear_modelfile(ruta_modelfile, ruta_jsonl)

            self._log("🚀 Creando modelo con Ollama...")
            self._log("   (esto puede tardar 2-5 minutos)")

            proc = subprocess.Popen(
                ["ollama", "create", "radioscript", "-f", ruta_modelfile],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for linea in proc.stdout:
                self._log(f"   {linea.rstrip()}")
            proc.wait()

            if proc.returncode == 0:
                self._log("✅ Modelo 'radioscript' creado correctamente.")
                self._log("   A partir de ahora se usará automáticamente.")
                self.after(0, lambda: messagebox.showinfo(
                    "Éxito", "Modelo 'radioscript' creado.\n"
                    "Se usará automáticamente en los próximos procesamientos.",
                    parent=self))
            else:
                self._log("❌ Error al crear el modelo. Revisa el log.")

        except Exception as e:
            self._log(f"❌ Error: {e}")
        finally:
            self.after(0, lambda: [
                self._actualizar_stats(),
                self.btn_entrenar.configure(
                    text="🚀  Crear Modelo Personalizado")
            ])

    def _log(self, texto: str):
        def _append():
            self.txt_log.configure(state=tk.NORMAL)
            self.txt_log.insert(tk.END, texto + "\n")
            self.txt_log.see(tk.END)
            self.txt_log.configure(state=tk.DISABLED)
        self.after(0, _append)