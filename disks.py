"""
disks.py - Reparto de bytes en discos simulados  (Persona 2)

stripe:   bytes -> m discos de datos (bloques de S bytes repartidos en turnos)
unstripe: m discos de datos -> bytes originales
fail:     marca discos como caídos (None)
degraded_bytes: lo que se leería SIN RAID (discos caídos = ceros)

Ejemplo con m = 3:
  bytes:   [b0][b1][b2][b3][b4][b5] ...   (cada bloque b tiene S bytes)
  disco 0: b0 b3 ...
  disco 1: b1 b4 ...
  disco 2: b2 b5 ...
Cada fila (b0 b1 b2) es una "franja" (stripe).
"""
import numpy as np


def stripe(data: bytes, m: int, S: int = 4096):
    """Reparte `data` entre m discos. Devuelve (lista_de_discos, longitud_original).

    Se rellena con ceros hasta un múltiplo de m*S para que todas las franjas
    estén completas; la longitud original permite recortar al final.
    """
    if m < 1 or S < 1:
        raise ValueError("m y S deben ser positivos")
    buf = np.frombuffer(bytes(data), dtype=np.uint8)
    orig_len = len(buf)

    franja = m * S
    n_franjas = -(-orig_len // franja)          # techo de la división
    relleno = np.zeros(n_franjas * franja, dtype=np.uint8)
    relleno[:orig_len] = buf

    # forma (franjas, discos, S): el bloque j de cada franja va al disco j
    bloques = relleno.reshape(n_franjas, m, S)
    discos = [bloques[:, j, :].reshape(-1).copy() for j in range(m)]
    return discos, orig_len


def unstripe(data_disks, orig_len: int, S: int = 4096) -> bytes:
    """Operación inversa de stripe."""
    m = len(data_disks)
    if any(d is None for d in data_disks):
        raise ValueError("Hay discos caídos: recupérelos primero o use degraded_bytes")
    if len({len(d) for d in data_disks}) != 1:
        raise ValueError("Todos los discos deben tener la misma longitud")
    n_franjas = len(data_disks[0]) // S
    bloques = np.stack([np.asarray(d, dtype=np.uint8).reshape(n_franjas, S)
                        for d in data_disks], axis=1)          # (franjas, m, S)
    return bloques.reshape(-1)[:orig_len].tobytes()


def fail(array, idx):
    """Devuelve una copia del arreglo con los discos `idx` caídos (None).

    No modifica el arreglo original.
    """
    idx = list(idx)
    if len(set(idx)) != len(idx):
        raise ValueError("Índices de disco repetidos")
    for i in idx:
        if not 0 <= i < len(array):
            raise IndexError(f"Disco {i} fuera de rango (0..{len(array) - 1})")
    return [None if i in idx else d for i, d in enumerate(array)]


def degraded_bytes(array, m: int, S: int, orig_len: int) -> bytes:
    """Bytes que se leerían sin reconstruir: los discos de datos caídos se leen
    como ceros. Sirve para mostrar la imagen "rota" (sin RAID)."""
    vivos = [d for d in array[:m] if d is not None]
    if not vivos:
        largo = -(-orig_len // (m * S)) * S
    else:
        largo = len(vivos[0])
    datos = [np.zeros(largo, dtype=np.uint8) if d is None else d for d in array[:m]]
    return unstripe(datos, orig_len, S)
