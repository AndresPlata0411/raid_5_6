"""
tests_core.py - Pruebas de gf.py, raid.py y disks.py

Ejecutar:  python tests_core.py
"""
import itertools
import unittest

import numpy as np

from gf import EXP, gf_mul, gf_inv, gf_mul_scalar
from raid import encode, recover, IrrecoverableError
from disks import stripe, unstripe, fail, degraded_bytes

rng = np.random.default_rng(2026)


def datos_aleatorios(n):
    return rng.integers(0, 256, n, dtype=np.uint8).tobytes()


class TestGF(unittest.TestCase):
    def test_tablas(self):
        self.assertEqual(EXP[8], 0x1D)      # x^8 = x^4 + x^3 + x^2 + 1
        self.assertEqual(EXP[255], 1)       # g^255 = 1
        self.assertEqual(len(set(EXP[:255].tolist())), 255)  # g genera todo

    def test_inverso(self):
        for a in range(1, 256):
            self.assertEqual(gf_mul(a, gf_inv(a)), 1)

    def test_propiedades(self):
        for _ in range(2000):
            a, b, c = (int(v) for v in rng.integers(0, 256, 3))
            self.assertEqual(gf_mul(a, b), gf_mul(b, a))
            self.assertEqual(gf_mul(a, b ^ c), gf_mul(a, b) ^ gf_mul(a, c))
            self.assertEqual(gf_mul(gf_mul(a, b), c), gf_mul(a, gf_mul(b, c)))

    def test_vectorizado_igual_a_escalar(self):
        arr = rng.integers(0, 256, 1000, dtype=np.uint8)
        for a in (0, 1, 2, 29, 255):
            esperado = [gf_mul(a, int(v)) for v in arr]
            self.assertEqual(gf_mul_scalar(a, arr).tolist(), esperado)


class TestDisks(unittest.TestCase):
    def test_ida_y_vuelta(self):
        for m in (3, 4, 8):
            for S in (512, 4096):
                for n in (0, 1, 7, m * S - 1, m * S, m * S + 1, 50_000):
                    x = datos_aleatorios(n)
                    discos, L = stripe(x, m, S)
                    self.assertEqual(len(discos), m)
                    self.assertEqual(unstripe(discos, L, S), x)

    def test_reparto_en_turnos(self):
        data = bytes([0] * 4 + [1] * 4 + [2] * 4)   # 3 bloques de S = 4
        discos, _ = stripe(data, 3, 4)
        self.assertEqual([d.tolist() for d in discos], [[0] * 4, [1] * 4, [2] * 4])

    def test_fail_no_modifica_original(self):
        arr = [np.zeros(4, np.uint8) for _ in range(5)]
        f = fail(arr, [1, 3])
        self.assertIsNone(f[1]); self.assertIsNone(f[3])
        self.assertTrue(all(d is not None for d in arr))

    def test_degradado(self):
        x = datos_aleatorios(4 * 512 * 3)
        discos, L = stripe(x, 4, 512)
        roto = degraded_bytes(fail(discos, [2]), 4, 512, L)
        self.assertEqual(len(roto), L)
        self.assertNotEqual(roto, x)


class TestRAID(unittest.TestCase):
    def preparar(self, m, level, n=30_000, S=512):
        x = datos_aleatorios(n)
        discos, L = stripe(x, m, S)
        return x, encode(discos, level), L, S

    def comprobar(self, original, arreglo, level, caidos):
        rec = recover(fail(arreglo, caidos), level)
        for a, b in zip(rec, arreglo):
            self.assertTrue(np.array_equal(a, b), f"falló con caídos={caidos}")

    def test_raid5_una_falla(self):
        for m in (3, 4, 8):
            _, arr, _, _ = self.preparar(m, 5)
            for i in range(m + 1):
                self.comprobar(None, arr, 5, [i])

    def test_raid6_una_y_dos_fallas(self):
        for m in (3, 4, 8):
            _, arr, _, _ = self.preparar(m, 6)
            n = m + 2
            for k in (1, 2):
                for caidos in itertools.combinations(range(n), k):
                    self.comprobar(None, arr, 6, list(caidos))

    def test_raid6_cuenta_m4(self):
        # Con m = 4 hay 6 discos -> C(6,2) = 15 parejas, todas recuperables
        _, arr, _, _ = self.preparar(4, 6)
        ok = 0
        for caidos in itertools.combinations(range(6), 2):
            rec = recover(fail(arr, caidos), 6)
            ok += all(np.array_equal(a, b) for a, b in zip(rec, arr))
        self.assertEqual(ok, 15)

    def test_irrecuperable(self):
        _, a5, _, _ = self.preparar(4, 5)
        _, a6, _, _ = self.preparar(4, 6)
        for c in itertools.combinations(range(5), 2):
            with self.assertRaises(IrrecoverableError):
                recover(fail(a5, c), 5)
        for c in itertools.combinations(range(6), 3):
            with self.assertRaises(IrrecoverableError):
                recover(fail(a6, c), 6)

    def test_flujo_completo(self):
        x, arr, L, S = self.preparar(4, 6, n=123_457)
        rec = recover(fail(arr, [0, 3]), 6)
        self.assertEqual(unstripe(rec[:4], L, S), x)


if __name__ == "__main__":
    unittest.main(verbosity=2)
