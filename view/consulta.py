from tkinter import ttk, messagebox
from funcaodb import deletar_usuario, buscar_usuario

# -------- Consulta -------- #
def create_consulta_tab(self):
    self.tab_consulta = ttk.Frame(self.notebook)
    self.notebook.add(self.tab_consulta, text="Consulta/Exclusão")
    ttk.Label(self.tab_consulta, text="ID:").grid(row=0, column=0)
    self.entry_pesquisa = ttk.Entry(self.tab_consulta, width=30); self.entry_pesquisa.grid(row=0, column=1)
    ttk.Button(self.tab_consulta, text="Buscar", command=self.buscar_usuario_tab).grid(row=0, column=2)
    ttk.Button(self.tab_consulta, text="Deletar", command=self.deletar_usuario_tab).grid(row=0, column=3)
    self.resultado_label = ttk.Label(self.tab_consulta, text=""); self.resultado_label.grid(row=1, column=0, columnspan=4)

def buscar_usuario_tab(self):
    user_id = self.entry_pesquisa.get().strip()
    usuario = buscar_usuario("id", user_id)
    if usuario: self.resultado_label.config(text=f"ID: {usuario[0]} | Nome: {usuario[1]} | CPF: {usuario[2]}")
    else: self.resultado_label.config(text="Usuário não encontrado.")

def deletar_usuario_tab(self):
    user_id = self.entry_pesquisa.get().strip()
    if not user_id: return
    if messagebox.askyesno("Confirmação", f"Deletar usuário {user_id}?"):
        if deletar_usuario(user_id):
            self.resultado_label.config(text="Usuário deletado.")
            self.refresh_users_table()
