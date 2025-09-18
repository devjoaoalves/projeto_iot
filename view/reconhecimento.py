import tkinter as tk
import cv2
import os
import numpy as np
from PIL import Image, ImageTk
from tkinter import ttk, messagebox
from main import FACE_SIZE, MODEL_PATH, TRAIN_DIR
from funcaodb import listar_usuarios, buscar_usuario
from geral import log

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

    # # Configurando o modelo de identificação de rosto
    # app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
    # app.prepare(ctx_id=0, det_size=(640, 640))

    # # Criando índice FAISS para guardar embeddings (512 dimensões)
    # dim = 512
    # index = faiss.IndexFlatL2(dim)
    # embeddings_db = []
    # names_db = []

    # def add_face_to_db(face_embedding, name):
    #     embedding = np.expand_dims(face_embedding, axis=0).astype('float32')
    #     index.add(embedding)
    #     embeddings_db.append(embedding)
    #     names_db.append(name)

    # def search_face(face_embedding, threshold=0.6):
    #     embedding = np.expand_dims(face_embedding, axis=0).astype('float32')
    #     D, I = index.search(embedding, 1)  # retorna distância e índice
    #     if len(I) > 0 and D[0][0] < threshold:  # quanto menor, mais parecido
    #         return names_db[I[0][0]], D[0][0]
    #     return None, None

    # # Acessando a webcam
    # cap = cv2.VideoCapture(0)

    # print("Pressione 'c' para cadastrar rosto, 'q' para sair.")

    # while True:
    #     ret, frame = cap.read()
    #     if not ret:
    #         break

    #     faces = app.get(frame)  # detecta rostos
    #     for face in faces:
    #         bbox = face.bbox.astype(int)
    #         emb = face.normed_embedding  # já normalizado

    #         x1, y1, x2, y2 = bbox
    #         cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

    #         name, dist = search_face(emb)
    #         if name:
    #             cv2.putText(frame, f"{name} ({dist:.2f})", (x1, y1-10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    #         else:
    #             cv2.putText(frame, "Desconhecido", (x1, y1-10),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

    #     cv2.imshow("Face Recognition", frame)

    #     key = cv2.waitKey(1) & 0xFF
    #     if key == ord('c') and len(faces) > 0:
    #         nome = input("Digite o nome da pessoa: ")
    #         add_face_to_db(faces[0].normed_embedding, nome)
    #         print(f"Rosto de {nome} cadastrado!")
    #     elif key == ord('q'):
    #         break

    # cap.release()
    # cv2.destroyAllWindows()


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