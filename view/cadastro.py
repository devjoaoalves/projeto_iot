import tkinter as tk
import cv2
import os
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from main import FACE_SIZE, TRAIN_DIR
from geral import log, validar_cpf
from reconhecimento import treinar_modelo
from funcaodb import inserir_usuario

# -------- Cadastro -------- #
def create_cadastro_tab(self):
    self.tab_cadastro = ttk.Frame(self.notebook)
    self.notebook.add(self.tab_cadastro, text="Cadastro")
    ttk.Label(self.tab_cadastro, text="Nome:").grid(row=0, column=0)
    self.entry_nome = ttk.Entry(self.tab_cadastro, width=30); self.entry_nome.grid(row=0, column=1)
    ttk.Label(self.tab_cadastro, text="ID:").grid(row=1, column=0)
    self.entry_id = ttk.Entry(self.tab_cadastro, width=30); self.entry_id.grid(row=1, column=1)
    ttk.Label(self.tab_cadastro, text="CPF:").grid(row=2, column=0)
    self.entry_cpf = ttk.Entry(self.tab_cadastro, width=30); self.entry_cpf.grid(row=2, column=1)

    self.camera_label = ttk.Label(self.tab_cadastro); self.camera_label.grid(row=0, column=2, rowspan=10)
    ttk.Button(self.tab_cadastro, text="Iniciar Câmera", command=self.start_camera).grid(row=3, column=0)
    self.btn_capturar = ttk.Button(self.tab_cadastro, text="Capturar Foto", command=self.capture_photo, state="disabled"); self.btn_capturar.grid(row=4, column=0)
    self.btn_salvar = ttk.Button(self.tab_cadastro, text="Salvar Cadastro", command=self.save_to_db, state="disabled"); self.btn_salvar.grid(row=5, column=0)
    self.status_label = ttk.Label(self.tab_cadastro, text=""); self.status_label.grid(row=6, column=0, columnspan=2)

def start_camera(self):
    if not self.capturing:
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Erro", "Câmera não encontrada")
            return
        self.capturing = True
        self.btn_capturar.config(state="normal")
        self.update_frame()
        log("Câmera iniciada.")
    else:
        self.capturing = False
        self.cap.release()
        self.camera_label.config(image="")
        self.btn_capturar.config(state="disabled")
        self.btn_salvar.config(state="disabled")
        log("Câmera parada.")

def update_frame(self):
    if self.capturing:
        ret, frame = self.cap.read()
        if ret:
            self.frame = frame
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA))
            imgtk = ImageTk.PhotoImage(image=img)
            self.camera_label.imgtk = imgtk
            self.camera_label.configure(image=imgtk)
        self.root.after(20, self.update_frame)

def capture_photo(self):
    if self.frame is not None:
        self.captured_image = self.frame.copy()
        self.status_label.config(text="Foto capturada!")
        self.btn_salvar.config(state="normal")
        log("Foto capturada para cadastro.")
    else:
        messagebox.showwarning("Aviso", "Nenhuma imagem capturada")

def save_to_db(self):
    nome, user_id, cpf = self.entry_nome.get().strip(), self.entry_id.get().strip(), self.entry_cpf.get().strip()
    if not all([nome, user_id, cpf]):
        messagebox.showwarning("Aviso", "Preencha todos os campos!"); return
    if not validar_cpf(cpf):
        messagebox.showwarning("Aviso", "CPF inválido!"); return
    if not hasattr(self, "captured_image"):
        messagebox.showwarning("Aviso", "Capture uma foto antes de salvar!"); return
    os.makedirs(TRAIN_DIR, exist_ok=True)
    foto_path = os.path.join(TRAIN_DIR, f"{user_id}.jpg")
    gray_resized = cv2.resize(cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2GRAY), FACE_SIZE)
    cv2.imwrite(foto_path, gray_resized)
    if inserir_usuario(user_id, nome, cpf, foto_path):
        treinar_modelo()
        self.status_label.config(text=f"Usuário {nome} cadastrado!")
        self.entry_nome.delete(0, tk.END); self.entry_id.delete(0, tk.END); self.entry_cpf.delete(0, tk.END)
        self.btn_salvar.config(state="disabled")
        self.refresh_users_table()
