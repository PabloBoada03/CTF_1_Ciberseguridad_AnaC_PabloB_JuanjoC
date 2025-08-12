#!/usr/bin/env python3
# Resolver RSA didactico (sin padding) para el reto
# Requiere: crypto_rsa_params.txt, rsa_p.txt (extraido de mascota.png), rsa_cipher.hex
# Uso: python3 rsa_solve_template.py

import re

def b2i(b): return int.from_bytes(b, 'big')
def i2b(i):
    if i == 0: return b"\x00"
    blen = (i.bit_length() + 7)//8
    return i.to_bytes(blen, 'big')

def inv_mod(a, m):
    t, new_t = 0, 1
    r, new_r = m, a
    while new_r != 0:
        q = r // new_r
        t, new_t = new_t, t - q*new_t
        r, new_r = new_r, r - q*new_r
    if r > 1: raise ValueError("no invertible")
    if t < 0: t += m
    return t

# Leer n y e
with open("crypto_rsa_params.txt","r") as f:
    t = f.read()
import re
n = int(re.search(r"n\s*=\s*(\d+)", t).group(1))
e = int(re.search(r"e\s*=\s*(\d+)", t).group(1))

# Leer p (del zip extraido) y calcular q, phi, d
with open("rsa_p.txt","r") as f:
    p = int(f.read().strip())
q = n // p
phi = (p-1)*(q-1)
d = inv_mod(e, phi)

# Descifrar el ciphertext (hex)
with open("rsa_cipher.hex","r") as f:
    c = int(f.read().strip(), 16)
m = pow(c, d, n)
pt = i2b(m)
print("Decrypted (fragment_F):", pt.decode("utf-8", errors="replace"))
