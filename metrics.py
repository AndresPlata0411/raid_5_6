"""Measurable reliability and capacity metrics for RAID 5 and RAID 6."""
from itertools import combinations
from math import comb

import numpy as np


def byte_accuracy(reference, candidate):
    """Percentage of original bytes preserved by a degraded read."""
    if len(reference) != len(candidate):
        raise ValueError("Los flujos deben tener la misma longitud")
    if not reference:
        return 100.0
    return 100.0 * sum(a == b for a, b in zip(reference, candidate)) / len(reference)


def failure_combinations(data_disks=4):
    """Count recoverable and total disk-failure sets for both RAID levels."""
    result = {}
    for level, parity in ((5, 1), (6, 2)):
        total = data_disks + parity
        recoverable = sum(comb(total, k) for k in range(parity + 1))
        result[str(level)] = {
            "disks": total,
            "parity_disks": parity,
            "recoverable_sets": recoverable,
            "all_sets": 2 ** total,
            "max_failures": parity,
            "usable_capacity": data_disks / total * 100,
            "unrecoverable_sets_by_count": [comb(total, k) for k in range(parity + 1, total + 1)],
        }
    return result


def data_loss_probability(level, disk_failure_probability, data_disks=4):
    """Probability of losing the array with independent identical disk failure rates."""
    if level not in (5, 6):
        raise ValueError("El nivel RAID debe ser 5 o 6")
    p = float(disk_failure_probability)
    if not 0 <= p <= 1:
        raise ValueError("La probabilidad debe estar entre 0 y 1")
    tolerance = 1 if level == 5 else 2
    total = data_disks + tolerance
    return sum(comb(total, k) * p ** k * (1 - p) ** (total - k)
               for k in range(tolerance + 1, total + 1))


def simulated_data_loss_probability(level, disk_failure_probability, trials=20000, seed=2026,
                                    data_disks=4):
    """Monte Carlo estimate, seeded for repeatable classroom demonstrations."""
    if trials < 1:
        raise ValueError("Se requiere al menos un ensayo")
    tolerance = 1 if level == 5 else 2 if level == 6 else None
    if tolerance is None:
        raise ValueError("El nivel RAID debe ser 5 o 6")
    p = float(disk_failure_probability)
    if not 0 <= p <= 1:
        raise ValueError("La probabilidad debe estar entre 0 y 1")
    total = data_disks + tolerance
    rng = np.random.default_rng(seed)
    losses = (rng.random((trials, total)) < p).sum(axis=1) > tolerance
    return float(losses.mean())


def probability_curve(data_disks=4, points=21):
    values = np.linspace(0, 0.2, points)
    return {"p": values.tolist(),
            "raid5": [data_loss_probability(5, p, data_disks) for p in values],
            "raid6": [data_loss_probability(6, p, data_disks) for p in values]}
