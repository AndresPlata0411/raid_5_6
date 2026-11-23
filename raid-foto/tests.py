"""Tests for the image demo and reliability metrics. Run: python tests.py"""
import itertools
import unittest

import numpy as np

from demo import analyze_image
from metrics import (byte_accuracy, data_loss_probability, failure_combinations,
                     simulated_data_loss_probability)


class TestMetrics(unittest.TestCase):
    def test_failure_set_counts_and_capacity(self):
        result = failure_combinations(4)
        self.assertEqual(result["5"]["disks"], 5)
        self.assertEqual(result["5"]["recoverable_sets"], 6)
        self.assertEqual(result["6"]["disks"], 6)
        self.assertEqual(result["6"]["recoverable_sets"], 22)
        self.assertAlmostEqual(result["5"]["usable_capacity"], 80)
        self.assertAlmostEqual(result["6"]["usable_capacity"], 100 * 4 / 6)

    def test_probability_bounds_and_raid6_is_safer(self):
        for p in (0, .01, .02, .1, .5, 1):
            r5 = data_loss_probability(5, p)
            r6 = data_loss_probability(6, p)
            self.assertGreaterEqual(r5, 0)
            self.assertLessEqual(r5, 1)
            self.assertGreaterEqual(r6, 0)
            self.assertLessEqual(r6, 1)
            if 0 < p < 1:
                self.assertLess(r6, r5)

    def test_simulation_is_repeatable(self):
        self.assertEqual(simulated_data_loss_probability(6, .02, 3000, 7),
                         simulated_data_loss_probability(6, .02, 3000, 7))

    def test_byte_accuracy(self):
        self.assertEqual(byte_accuracy(b"abcd", b"abXd"), 75)
        self.assertEqual(byte_accuracy(b"", b""), 100)


class TestImageDemo(unittest.TestCase):
    def test_roundtrip_and_recoverable_scenarios(self):
        width, height = 32, 24
        raw = np.random.default_rng(42).integers(0, 256, width * height * 3, dtype=np.uint8).tobytes()
        no_failure = analyze_image(raw, width, height, 0)
        self.assertTrue(no_failure["raid"]["5"]["recoverable"])
        self.assertTrue(no_failure["raid"]["6"]["recoverable"])
        self.assertEqual(no_failure["raid"]["6"]["accuracy"], 100)
        one = analyze_image(raw, width, height, 1)
        self.assertTrue(one["raid"]["5"]["recoverable"])
        two = analyze_image(raw, width, height, 2)
        self.assertFalse(two["raid"]["5"]["recoverable"])
        self.assertTrue(two["raid"]["6"]["recoverable"])
        three = analyze_image(raw, width, height, 3)
        self.assertFalse(three["raid"]["5"]["recoverable"])
        self.assertFalse(three["raid"]["6"]["recoverable"])

    def test_invalid_image_shape(self):
        with self.assertRaises(ValueError):
            analyze_image(b"too short", 4, 4, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
