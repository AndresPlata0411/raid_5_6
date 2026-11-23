"""
gf.py - Aritmética en el cuerpo finito GF(2^8)  (Persona 1)

Cada byte (0..255) se ve como un polinomio de grado < 8 con coeficientes en F2.
  - Suma y resta: XOR (^).
  - Multiplicación: módulo el polinomio primitivo x^8 + x^4 + x^3 + x^2 + 1 (0x11D).

Para multiplicar rápido usamos tablas de logaritmos con el generador g = 2:
  EXP[i] = g^i        LOG[g^i] = i
  a * b  = EXP[LOG[a] + LOG[b]]   (si a, b != 0)
"""
import numpy as np

PRIM = 0x11D   # polinomio primitivo x^8 + x^4 + x^3 + x^2 + 1
G = 2          # generador del grupo multiplicativo (255 elementos)

# EXP tiene 512 posiciones para no tener que hacer "% 255" al sumar dos logaritmos
# (LOG[a] + LOG[b] <= 254 + 254 = 508).
EXP = np.zeros(512, dtype=np.uint8)
LOG = np.zeros(256, dtype=np.int32)   # LOG[0] no está definido; nunca se usa


def _construir_tablas():
    x = 1
    for i in range(255):
        EXP[i] = x
        LOG[x] = i
        x <<= 1              # multiplicar por g = 2 (correr un bit a la izquierda)
        if x & 0x100:        # si el grado llegó a 8, reducir módulo el polinomio
            x ^= PRIM
    for i in range(255, 512):
        EXP[i] = EXP[i - 255]   # g^255 = 1, así que la tabla se repite


_construir_tablas()


# ---------- Operaciones con escalares (un solo byte) ----------

def gf_add(a: int, b: int) -> int:
    """Suma (y resta) en GF(2^8): XOR."""
    return a ^ b


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return int(EXP[LOG[a] + LOG[b]])


def gf_inv(a: int) -> int:
    """Inverso multiplicativo: a * gf_inv(a) = 1."""
    if a == 0:
        raise ZeroDivisionError("0 no tiene inverso en GF(2^8)")
    return int(EXP[255 - LOG[a]])


def gf_div(a: int, b: int) -> int:
    return gf_mul(a, gf_inv(b))


def gf_pow_g(i: int) -> int:
    """g^i, con g = 2."""
    return int(EXP[i % 255])


# ---------- Operaciones sobre discos completos (arreglos numpy) ----------

def gf_mul_scalar(a: int, arr: np.ndarray) -> np.ndarray:
    """Multiplica cada byte de `arr` por el escalar `a` en GF(2^8).

    Vectorizado con numpy: un disco puede tener millones de bytes.
    """
    arr = np.asarray(arr, dtype=np.uint8)
    if a == 0:
        return np.zeros_like(arr)
    res = EXP[LOG[arr] + LOG[a]]
    res[arr == 0] = 0        # 0 * a = 0 (LOG[0] no tiene sentido)
    return res
