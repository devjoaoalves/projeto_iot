import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
from PIL import Image, ImageTk
import sqlite3
import numpy as np
import re
import datetime
from main import DB_NAME, FACE_SIZE, MODEL_PATH, TRAIN_DIR


# ---------------- LOG ---------------- #
def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

# ---------------- BANCO DE DADOS ---------------- #
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL,
            foto_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    log("Banco de dados inicializado.")

def inserir_usuario(user_id, nome, cpf, foto_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO usuarios (id, nome, cpf, foto_path) VALUES (?, ?, ?, ?)",
                  (int(user_id), nome, cpf, foto_path))
        conn.commit()
        log(f"Usuário {user_id} inserido: {nome}, CPF {cpf}")
        inserted = True
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "ID já cadastrado")
        inserted = False
    finally:
        conn.close()
    return inserted

def editar_usuario(user_id, novo_nome, novo_cpf):
    try:
        uid = int(user_id)
    except ValueError:
        return False
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("UPDATE usuarios SET nome=?, cpf=? WHERE id=?", (novo_nome, novo_cpf, uid))
        conn.commit()
        success = (c.rowcount > 0)
        if success:
            log(f"Usuário {uid} atualizado para Nome={novo_nome}, CPF={novo_cpf}")
    except Exception as e:
        log(f"Erro ao editar usuário {uid}: {e}")
        success = False
    finally:
        conn.close()
    return success

def buscar_usuario(campo, valor):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if campo == "id":
        try:
            valor = int(valor)
        except ValueError:
            conn.close()
            return None
    c.execute(f"SELECT * FROM usuarios WHERE {campo}=?", (valor,))
    result = c.fetchone()
    conn.close()
    return result

def listar_usuarios():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios ORDER BY id")
    result = c.fetchall()
    conn.close()
    return result

def deletar_usuario(user_id):
    try:
        uid = int(user_id)
    except ValueError:
        return False
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT foto_path FROM usuarios WHERE id=?", (uid,))
    foto = c.fetchone()
    if foto and os.path.exists(foto[0]):
        try:
            os.remove(foto[0])
            log(f"Foto {foto[0]} removida.")
        except Exception as e:
            log(f"Erro ao remover foto {foto[0]}: {e}")
    c.execute("DELETE FROM usuarios WHERE id=?", (uid,))
    conn.commit()
    conn.close()
    treinar_modelo()
    log(f"Usuário {uid} excluído.")
    return True

# ---------------- CPF ---------------- #
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)  # só números
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = ((soma1 * 10) % 11) % 10
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = ((soma2 * 10) % 11) % 10
    return dig1 == int(cpf[9]) and dig2 == int(cpf[10])

# ---------------- RECONHECIMENTO ---------------- #
def load_and_prepare_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    img = cv2.resize(img, FACE_SIZE)
    return img

def treinar_modelo():
    os.makedirs(TRAIN_DIR, exist_ok=True)
    usuarios = listar_usuarios()
    faces, ids = [], []
    for usuario in usuarios:
        user_id, foto_path = int(usuario[0]), usuario[3]
        if os.path.exists(foto_path):
            img = load_and_prepare_image(foto_path)
            if img is not None:
                faces.append(img)
                ids.append(user_id)
    if faces:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(ids))
        recognizer.save(MODEL_PATH)
        log("Modelo treinado e salvo.")
    else:
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            log("Modelo removido (sem dados).")

def reconhecer_rosto(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    if not os.path.exists(MODEL_PATH):
        return None, 0

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    for (x, y, w, h) in faces:
        roi = cv2.resize(gray[y:y+h, x:x+w], FACE_SIZE)
        user_id, conf = recognizer.predict(roi)
        if conf < 60:
            log(f"Reconhecido ID={user_id} com confiança {conf:.1f}")
            return str(user_id), conf
        else:
            log(f"Rosto não identificado (conf {conf:.1f})")
            return None, conf
    return None, 0

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

    # -------- Reconhecimento -------- #
    def create_reconhecimento_tab(self):
        self.tab_reconhecimento = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reconhecimento, text="Reconhecimento Facial")
        self.camera_label_rec = ttk.Label(self.tab_reconhecimento); self.camera_label_rec.pack()
        self.btn_start_rec = ttk.Button(self.tab_reconhecimento, text="Iniciar", command=self.start_recognition); self.btn_start_rec.pack()
        self.status_rec_label = ttk.Label(self.tab_reconhecimento, text=""); self.status_rec_label.pack()
        self.recognizing = False

    def start_recognition(self):
        if not self.recognizing:
            self.rec = cv2.VideoCapture(0)
            if not self.rec.isOpened():
                messagebox.showerror("Erro", "Não foi possível acessar a câmera"); return
            self.recognizing = True; self.update_recognition(); self.btn_start_rec.config(text="Parar")
            log("Reconhecimento iniciado.")
        else:
            self.recognizing = False; self.rec.release()
            self.camera_label_rec.config(image=""); self.btn_start_rec.config(text="Iniciar"); self.status_rec_label.config(text="")
            log("Reconhecimento parado.")

    def update_recognition(self):
        if self.recognizing:
            ret, frame = self.rec.read()
            if ret:
                user_id, conf = reconhecer_rosto(frame)
                display_frame = frame.copy()
                if user_id:
                    usuario = buscar_usuario("id", user_id)
                    if usuario:
                        cv2.putText(display_frame, usuario[1], (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                        self.status_rec_label.config(text=f"Reconhecido: {usuario[1]}")
                cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image); imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label_rec.imgtk = imgtk; self.camera_label_rec.configure(image=imgtk)
            self.root.after(20, self.update_recognition)

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