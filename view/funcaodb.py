import os
import sqlite3
from tkinter import messagebox
from main import DB_NAME
from geral import log
from reconhecimento import treinar_modelo

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
