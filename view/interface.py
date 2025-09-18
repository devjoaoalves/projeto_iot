import tkinter as ttk

# ---------------- INTERFACE ---------------- #
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Cadastro Facial")
        self.root.geometry("1100x700")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')
        self.create_cadastro_tab()
        self.create_consulta_tab()
        self.create_reconhecimento_tab()
        self.create_usuarios_tab()
        self.capturing = False
        self.frame = None