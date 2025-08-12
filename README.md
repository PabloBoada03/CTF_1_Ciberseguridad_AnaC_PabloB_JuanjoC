# CTF Guiado — "Operación Fortuna"

**Objetivo:** Unir evidencias de varias técnicas para formar la bandera final:
```
CTF{A-B-C-D-E-F-G}
```
Cada fragmento proviene de un tema distinto (OSINT/redes sociales, César, Vigenère, hashes, DES, AES, RSA, firmas, esteganografía).

> Nota: Interpretaré "Ashes" como **hashes** (MD5/SHA-256).

---

## Estructura de archivos
```
profile.html                 # Perfil social (OSINT)
selfie.jpg                   # Tiene un comentario JPEG con un mensaje cifrado con César
mascota.png                  # Imagen PNG con un ZIP oculto (esteganografía por archivo adjunto)
hashes.txt                   # Huellas MD5/SHA-256 a verificar
crypto_rsa_params.txt        # n y e (RSA) — falta p
rsa_cipher.hex               # Texto cifrado con RSA (sin padding, didáctico)
mensaje_final.txt            # Mensaje para validar firma
firma.hex                    # Firma digital simplificada de mensaje_final.txt (didáctico)
rsa_solve_template.py        # Script de ayuda para descifrar RSA cuando tengas p
```

Dentro del ZIP escondido en `mascota.png` encontrarás:
```
rsa_p.txt                    # El primo p de RSA
nota_vigenere.txt            # Instrucciones cifradas con Vigenère
semilla_para_aes.txt         # Texto a usar con DES (ECB) para derivar IV de AES
```

---

## Paso 1 — OSINT (redes sociales simuladas)
1. Abre `profile.html`. Recolecta datos obvios: **mascota** (nombre), **fecha de adopción**, gustos, etc.
2. Tip: Las **iniciales** de los hashtags de la primera publicación forman una **palabra**.
3. Guarda: `A = <nombre de la mascota en MAYUSCULAS>`.

## Paso 2 — César (comentario JPEG)
1. Abre `selfie.jpg` y extrae el **comentario JPEG** (en Linux: `exiftool -Comment selfie.jpg` o `strings selfie.jpg | head`).
2. Verás un texto en mayúsculas cifrado. Aplícale **César** (prueba desplazamientos; pista: es **+7**).
3. El texto revelará la **palabra clave de Vigenère**. Apúntala. Define `B = esa palabra` en MAYÚSCULAS.

## Paso 3 — Esteganografía (ZIP adjunto a PNG)
1. Inspecciona `mascota.png`. Truco: muchos visores ZIP detectan un ZIP **anexado** al final del archivo.
   - Ejemplos: `binwalk -e mascota.png` o `unzip -l mascota.png` o cambia la extensión a `.zip` y ábrelo.
2. Extrae el contenido: `rsa_p.txt`, `nota_vigenere.txt`, `semilla_para_aes.txt`.

## Paso 4 — Vigenère
1. `nota_vigenere.txt` está cifrada con **Vigenère** usando la palabra clave del Paso 2.
2. Descifra y **sigue sus instrucciones** (sobre DES y AES).

## Paso 5 — Hashes (MD5/SHA-256)
1. Abre `hashes.txt`. Verifica qué **frases** del `profile.html` (o deducidas) generan esos hashes.
2. Confirma al menos:
   - `SHA256(toby-2019-12-24)`
   - `MD5(CAFETERI)`
3. Define `C = la frase que coincide con el SHA-256` (en minúsculas tal cual).

## Paso 6 — DES (ECB) → Fragmento D
1. De la nota Vigenère obtendrás: **CLAVE DES = "CAFETERI"**, **MODO = ECB**, **entrada = semilla_para_aes.txt**.
2. Cifra con DES-ECB y **toma los primeros 8 bytes** del resultado **en hex** como `D`.
   - Ejemplo con OpenSSL (Linux/Mac):
     ```bash
     # Obtener clave en HEX de "CAFETERI"
     printf "CAFETERI" | xxd -p -c 256  # (usa este HEX como -K)
     # Cifrar (ECB; si tu herramienta no permite -nopad, acepta el padding por defecto para este reto)
     openssl enc -des-ecb -in semilla_para_aes.txt -nosalt -K <HEX_DE_LA_CLAVE> -out des_out.bin
     xxd -p -c 256 des_out.bin | cut -c1-16  # primeros 8 bytes en hex => D
     ```

## Paso 7 — AES (CBC) → Fragmento E
1. **CLAVE AES-256** = `SHA256('toby-2019-12-24')` en HEX (del Paso 5).
2. **IV** = el HEX obtenido en `D` (16 hex = 8 bytes). Para AES-CBC el IV debe ser 16 bytes; **duplica ese bloque** para formar 16 bytes: `IV = D || D`.
3. Texto a cifrar (UTF-8): `EL CAFE ES VIDA`.
4. Cifra con **AES-256-CBC** y toma los **primeros 8 bytes** del ciphertext en hex como `E`.
   - Ejemplo con OpenSSL:
     ```bash
     # clave en HEX ya la tienes (SHA-256)
     ivhex="<D><D>"           # concatena D dos veces
     echo -n "EL CAFE ES VIDA" |        openssl enc -aes-256-cbc -K <CLAVE_HEX> -iv "$ivhex" -nosalt -out aes_out.bin
     xxd -p -c 256 aes_out.bin | cut -c1-16  # => E
     ```

## Paso 8 — RSA (descifrado) → Fragmento F
1. Tienes `crypto_rsa_params.txt` (con `n` y `e`) y en el ZIP oculto `rsa_p.txt` (el primo `p`).
2. Ejecuta `python3 rsa_solve_template.py` en la carpeta con esos archivos y `rsa_cipher.hex`.
3. El script imprimirá `fragment_F` (texto corto). Ese será `F`.

## Paso 9 — Firma digital (verificación) → Fragmento G
Este es un esquema **didáctico sin padding** (NO usar en producción).
1. Calcula `H = SHA-256(mensaje_final.txt)` (como entero grande).
2. Lee `firma.hex`, conviértelo a entero `s`. Verifica: `pow(s, e, n) == H`.
3. Si coincide, `G = OK`. Si no, `G = FAIL`.

---

## Ensamblado de la bandera
- `A` = nombre de la mascota en MAYÚSCULAS (del Paso 1).
- `B` = palabra revelada en el Paso 2 (clave Vigenère) en MAYÚSCULAS.
- `C` = la frase exacta que produjo el SHA-256 (en minúsculas; del Paso 5).
- `D` = primeros 8 bytes (hex) del resultado DES-ECB (Paso 6).
- `E` = primeros 8 bytes (hex) del resultado AES-256-CBC (Paso 7).
- `F` = texto corto descifrado por RSA (Paso 8).
- `G` = resultado de la verificación de firma (OK/FAIL, Paso 9).

Formato final:
```
CTF{A-B-C-D-E-F-G}
```

---

## Consejos
- Documenta cada paso (comandos usados y explicaciones). Cuando digas **"terminé"**, te pasaré un segundo reto **sin guía** y te pediré tu documentación para darte feedback (qué estuvo bien/mal y soluciones).
- Si no tienes `openssl`, puedes usar herramientas/librerías equivalentes (por ejemplo, Python con `pycryptodome`), o laboratorios online.
- El ZIP está escondido por **adjuntar** bytes de ZIP al final de un PNG — técnica de esteganografía simple para CTF.

¡Éxitos!
