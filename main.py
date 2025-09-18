import tkinter as tk
import os
from main import TRAIN_DIR
from view.funcaodb import init_db
from view.reconhecimento import treinar_modelo
from view.interface import App

# ---------------- CONFIG ---------------- #
DB_NAME = "usuarios.db"
TRAIN_DIR = "fotos"
MODEL_PATH = "modelo_lbph.yml"
FACE_SIZE = (200, 200)


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    init_db()
    os.makedirs(TRAIN_DIR, exist_ok=True)
    treinar_modelo()
    root = tk.Tk(); app = App(root) 
    root.mainloop()