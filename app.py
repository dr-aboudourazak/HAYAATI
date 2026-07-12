"""
POINT D'ENTRÉE GRAPHIQUE UNIQUE (APP.PY)
Lance l'interface visuelle moderne sur une seule et même fenêtre.
"""
import tkinter as tk
from gui.app_visuelle import HayaatiApp

if __name__ == "__main__":
    root = tk.Tk()
    app = HayaatiApp(root)
    root.mainloop()
