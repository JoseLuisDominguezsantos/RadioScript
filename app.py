# ─── RadioScript · app.py ────────────────────────────────────────────────────
# Punto de entrada principal de la aplicación
from ui.ventana import Ventana


def main():
    app = Ventana()
    app.mainloop()


if __name__ == "__main__":
    main()