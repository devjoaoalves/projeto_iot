import re
import datetime

# ---------------- LOG ---------------- #
def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

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
