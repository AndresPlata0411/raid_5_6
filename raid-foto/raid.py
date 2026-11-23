"""
raid.py - Codificación y recuperación RAID 5 y RAID 6  (Persona 1)

Un "arreglo" es una lista de discos (arreglos numpy uint8 de igual longitud):
  RAID 5: [D0, ..., D(m-1), P]
  RAID 6: [D0, ..., D(m-1), P, Q]
Un disco caído se representa con None.

Fórmulas (suma = XOR, producto en GF(2^8), g = 2):
  P = D0 + D1 + ... + D(m-1)
  Q = g^0*D0 + g^1*D1 + ... + g^(m-1)*D(m-1)

Como sabemos QUÉ discos fallaron, son borrados (no errores):
  RAID 5 es un código de paridad con d = 2  -> recupera 1 borrado.
  RAID 6 es un código MDS (Reed-Solomon) con d = 3 -> recupera 2 borrados.
"""
import numpy as np

from gf import gf_mul_scalar, gf_pow_g, gf_inv


class IrrecoverableError(Exception):
    """Hay más discos caídos que paridades: los datos no se pueden recuperar."""


# ---------- Paridades ----------

def compute_p(data_disks):
    """P = XOR de todos los discos de datos."""
    p = np.zeros_like(data_disks[0])
    for d in data_disks:
        p ^= d
    return p


def compute_q(data_disks):
    """Q = suma de g^i * D_i en GF(2^8)."""
    q = np.zeros_like(data_disks[0])
    for i, d in enumerate(data_disks):
        q ^= gf_mul_scalar(gf_pow_g(i), d)
    return q


def encode(data_disks, level: int):
    """Agrega los discos de paridad. Devuelve el arreglo completo."""
    _validar_nivel(level)
    data_disks = [np.asarray(d, dtype=np.uint8) for d in data_disks]
    if len(data_disks) < 2:
        raise ValueError("Se necesitan al menos 2 discos de datos")
    if level == 6 and len(data_disks) > 255:
        raise ValueError("RAID 6 con g = 2 admite como máximo 255 discos de datos")
    if len({len(d) for d in data_disks}) != 1:
        raise ValueError("Todos los discos deben tener la misma longitud")

    array = [d.copy() for d in data_disks]
    array.append(compute_p(data_disks))
    if level == 6:
        array.append(compute_q(data_disks))
    return array


# ---------- Recuperación ----------

def recover(array, level: int):
    """Reconstruye los discos caídos (None). Devuelve un arreglo nuevo y completo.

    Lanza IrrecoverableError si hay más fallas que discos de paridad.
    """
    _validar_nivel(level)
    n_par = 1 if level == 5 else 2
    m = len(array) - n_par
    if m < 2:
        raise ValueError("Arreglo demasiado pequeño para este nivel de RAID")

    caidos = [i for i, d in enumerate(array) if d is None]
    if len(caidos) > n_par:
        raise IrrecoverableError(
            f"RAID {level} tolera {n_par} falla(s) y hay {len(caidos)} discos caídos: {caidos}")

    out = [None if d is None else np.asarray(d, dtype=np.uint8).copy() for d in array]
    if not caidos:
        return out

    if level == 5:
        _recuperar_raid5(out, m, caidos[0])
    else:
        _recuperar_raid6(out, m, caidos)
    return out


def _recuperar_raid5(out, m, x):
    iP = m
    if x == iP:                       # cayó la paridad: se recalcula
        out[iP] = compute_p(out[:m])
        return
    # D_x = P + (suma de los demás datos)
    dx = out[iP].copy()
    for i in range(m):
        if i != x:
            dx ^= out[i]
    out[x] = dx


def _recuperar_raid6(out, m, caidos):
    iP, iQ = m, m + 1
    datos_caidos = [i for i in caidos if i < m]

    if len(datos_caidos) == 1:
        x = datos_caidos[0]
        if out[iP] is not None:
            # Con P basta (igual que RAID 5)
            dx = out[iP].copy()
            for i in range(m):
                if i != x:
                    dx ^= out[i]
        else:
            # Cayeron D_x y P: usamos Q.
            # Q' = Q + suma_{i != x} g^i D_i = g^x D_x   ->   D_x = Q' / g^x
            qp = out[iQ].copy()
            for i in range(m):
                if i != x:
                    qp ^= gf_mul_scalar(gf_pow_g(i), out[i])
            dx = gf_mul_scalar(gf_inv(gf_pow_g(x)), qp)
        out[x] = dx

    elif len(datos_caidos) == 2:
        # Cayeron D_x y D_y (P y Q están vivos). Sistema de 2 ecuaciones:
        #   P' = D_x + D_y
        #   Q' = g^x D_x + g^y D_y
        # => D_x = (Q' + g^y P') / (g^x + g^y),   D_y = P' + D_x
        x, y = datos_caidos
        pp = out[iP].copy()
        qp = out[iQ].copy()
        for i in range(m):
            if i not in (x, y):
                pp ^= out[i]
                qp ^= gf_mul_scalar(gf_pow_g(i), out[i])
        gx, gy = gf_pow_g(x), gf_pow_g(y)
        denom_inv = gf_inv(gx ^ gy)          # gx != gy porque x != y y m <= 255
        dx = gf_mul_scalar(denom_inv, qp ^ gf_mul_scalar(gy, pp))
        out[x] = dx
        out[y] = pp ^ dx

    # Con todos los datos ya presentes, se recalculan las paridades perdidas
    if out[iP] is None:
        out[iP] = compute_p(out[:m])
    if out[iQ] is None:
        out[iQ] = compute_q(out[:m])


def _validar_nivel(level):
    if level not in (5, 6):
        raise ValueError("level debe ser 5 o 6")
