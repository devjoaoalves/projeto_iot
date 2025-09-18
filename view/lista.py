import tkinter as tk
from tkinter import ttk, messagebox
from funcaodb import deletar_usuario, listar_usuarios, editar_usuario
from geral import validar_cpf

# -------- Lista Usuários -------- #
def create_usuarios_tab(self):
    self.tab_usuarios = ttk.Frame(self.notebook)
    self.notebook.add(self.tab_usuarios, text="Usuários")
    cols = ("id", "nome", "cpf", "foto_path")
    self.tree = ttk.Treeview(self.tab_usuarios, columns=cols, show="headings", height=20)
    for c in cols: self.tree.heading(c, text=c.upper())
    self.tree.grid(row=0, column=0, columnspan=5, sticky="nsew")
    ttk.Button(self.tab_usuarios, text="Atualizar", command=self.refresh_users_table).grid(row=1, column=0)
    ttk.Button(self.tab_usuarios, text="Editar", command=self.open_edit_dialog).grid(row=1, column=1)
    ttk.Button(self.tab_usuarios, text="Deletar", command=self.delete_selected_user).grid(row=1, column=2)
    self.refresh_users_table()

def refresh_users_table(self):
    for i in self.tree.get_children(): self.tree.delete(i)
    for usuario in listar_usuarios(): self.tree.insert("", "end", values=usuario)

def delete_selected_user(self):
    sel = self.tree.selection()
    if not sel: return
    user_id = self.tree.item(sel[0], "values")[0]
    if messagebox.askyesno("Confirmação", f"Excluir {user_id}?"):
        if deletar_usuario(user_id): self.refresh_users_table()

def open_edit_dialog(self):
    sel = self.tree.selection()
    if not sel: return
    values = self.tree.item(sel[0], "values")
    user_id, nome_atual, cpf_atual = values[0], values[1], values[2]
    top = tk.Toplevel(self.root); top.title(f"Editar {user_id}")
    ttk.Label(top, text=f"ID: {user_id}").grid(row=0, column=0)
    entry_nome = ttk.Entry(top, width=30); entry_nome.grid(row=1, column=1); entry_nome.insert(0, nome_atual)
    entry_cpf = ttk.Entry(top, width=30); entry_cpf.grid(row=2, column=1); entry_cpf.insert(0, cpf_atual)
    def save_edits():
        novo_nome, novo_cpf = entry_nome.get().strip(), entry_cpf.get().strip()
        if not validar_cpf(novo_cpf):
            messagebox.showwarning("Aviso", "CPF inválido!"); return
        if editar_usuario(user_id, novo_nome, novo_cpf):
            self.refresh_users_table(); top.destroy()
    ttk.Button(top, text="Salvar", command=save_edits).grid(row=3, column=0)
    ttk.Button(top, text="Cancelar", command=top.destroy).grid(row=3, column=1)