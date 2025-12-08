import base64, os, time, struct, hmac, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes  # ✅ Add this import
from cryptography.hazmat.backends import default_backend  # ✅ Required

def derive_key_sha512(password: str, salt: bytes, iterations: int = 100_000) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA512(),  # ✅ Use this, not hashlib.sha256()
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    ).derive(password.encode())

def derive_key(password: str, salt: bytes, iterations: int = 100_000) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),  # ✅ Use this, not hashlib.sha256()
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    ).derive(password.encode())

def encrypt_secret(secret: str, password: str) -> str:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    data = secret.encode()
    enc = aesgcm.encrypt(nonce, data, None)
    return base64.b64encode(salt + nonce + enc).decode()

def decrypt_secret(payload: str, password: str) -> str:
    raw = base64.b64decode(payload)
    salt, nonce, ct = raw[:16], raw[16:28], raw[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()

def generate_totp(secret: str, digits=6, interval=30, algo='sha512') -> str:
    key = base64.b32decode(secret, casefold=True)
    counter = struct.pack(">Q", int(time.time() / interval))
    h = hmac.new(key, counter, getattr(hashlib, algo)).digest()
    o = h[-1] & 0x0F
    code = struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff
    return str(code % (10 ** digits)).zfill(digits)

def encrypt_bytes(data: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    enc = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + enc

def decrypt_bytes(data: bytes, password: str) -> bytes:
    salt, nonce, ct = data[:16], data[16:28], data[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)

