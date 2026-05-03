"""
main.py
--------
Ponto de entrada do sistema de navegação por algoritmos de busca.
Inicializa a janela Tkinter e delega tudo à camada gui/.

Execute com:
    python main.py
"""

import tkinter as tk
from gui.interface import NavigationApp


def main() -> None:
    root = tk.Tk()
    root.minsize(900, 640)

    # Centraliza a janela na tela
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 1100, 740
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    app = NavigationApp(root)  # noqa: F841
    root.mainloop()


if __name__ == "__main__":
    main()
