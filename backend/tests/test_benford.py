# Origen: media-scraper, rama feature/setup-inicial, commit a3ef81d2e533d0c9e58e144ee6c4c863a43961cc,
# archivo tests/test_benford.py. Solo la clase MathematicsTests (líneas 64-115), con los imports ajustados.
# RepositoryTests y EndpointTests no se trasplantan: dependen de MongoDB y de la API de media-scraper.
"""Controlled mathematical tests."""
from decimal import Decimal
import math
import unittest

from truematch.domain.audience_audit.benford import analyze_values, benford_probabilities, first_significant_digit


class MathematicsTests(unittest.TestCase):
    def test_theoretical_probabilities(self):
        probabilities = benford_probabilities()
        self.assertEqual(len(probabilities), 9)
        self.assertAlmostEqual(sum(probabilities), 1)
        self.assertAlmostEqual(probabilities[0], math.log10(2))
        self.assertAlmostEqual(probabilities[8], math.log10(10 / 9))
        self.assertTrue(all(a > b for a, b in zip(probabilities, probabilities[1:])))

    def test_significant_digits_without_log_rounding_or_integer_overflow(self):
        for value, digit in [(1, 1), (999, 9), (1000, 1), (0.0042, 4), (7e-200, 7),
                             (Decimal('0.00000091'), 9), (10**200 + 1, 1), (9.999, 9)]:
            with self.subTest(value=value):
                self.assertEqual(first_significant_digit(value), digit)

    def test_known_counts_mad_and_chi_squared(self):
        result = analyze_values([1, 10, 200, 90])
        counts = [2, 1, 0, 0, 0, 0, 0, 0, 1]
        p = benford_probabilities()
        self.assertEqual([row['observed_count'] for row in result['distribution']], counts)
        self.assertEqual([row['observed_probability'] for row in result['distribution']], [c / 4 for c in counts])
        self.assertAlmostEqual(result['mad'], sum(abs(c / 4 - q) for c, q in zip(counts, p)) / 9)
        self.assertAlmostEqual(result['chi_squared'], sum((c - 4*q)**2 / (4*q) for c, q in zip(counts, p)))
        self.assertAlmostEqual(sum(row['observed_percent'] for row in result['distribution']), 100)
        self.assertEqual(result, analyze_values([90, 200, 10, 1]))

    def test_exclusions_are_separate_and_original_numbers_only(self):
        values = [None, 0, 0.0, -5, 'N/A', '1.2K', '123', True, float('nan'), float('inf'), {}, 12]
        result = analyze_values(values)
        self.assertEqual(result['exclusions'], dict(missing=1, zero=2, negative=1, invalid=7))
        self.assertEqual((result['total_records'], result['valid_records'], result['excluded_records']), (12, 1, 11))
        for value in values[:-1]:
            self.assertIsNone(first_significant_digit(value))

    def test_empty_is_not_a_fictional_zero_distribution(self):
        result = analyze_values([])
        self.assertEqual(result['status'], 'empty')
        self.assertIsNone(result['mad'])
        self.assertIsNone(result['chi_squared'])
        self.assertTrue(all(row['observed_probability'] is None for row in result['distribution']))

    def test_small_sample_and_expected_count_boundary(self):
        small = analyze_values(list(range(1, 11)))
        self.assertFalse(small['expected_counts_sufficient'])
        self.assertTrue(small['low_expected_digits'])
        self.assertTrue(any('Muestra reducida' in warning for warning in small['warnings']))
        self.assertFalse(analyze_values([1] * 109)['expected_counts_sufficient'])
        large = analyze_values([1] * 110)
        self.assertTrue(large['expected_counts_sufficient'])
        self.assertFalse(large['inference_performed'])
        self.assertIsNone(large['p_value'])
        self.assertIn('no demuestra', large['disclaimer'])
