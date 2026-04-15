"""Tests for helper and validator utility functions."""

import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import generate_id, hash_string, paginate, slugify
from validators import validate_email, validate_password_strength, validate_required_fields


class TestSlugify(unittest.TestCase):
    """Tests for the slugify helper."""

    def test_basic_slug(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_strips_special_chars(self):
        self.assertEqual(slugify("Price: $100!"), "price-100")

    def test_collapses_whitespace(self):
        self.assertEqual(slugify("  lots   of   space  "), "lots-of-space")


class TestGenerateId(unittest.TestCase):
    def test_length_is_32(self):
        self.assertEqual(len(generate_id()), 32)

    def test_uniqueness(self):
        ids = {generate_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)


class TestHashString(unittest.TestCase):
    def test_sha256_deterministic(self):
        h1 = hash_string("hello")
        h2 = hash_string("hello")
        self.assertEqual(h1, h2)

    def test_different_inputs_differ(self):
        self.assertNotEqual(hash_string("a"), hash_string("b"))


class TestPaginate(unittest.TestCase):
    def test_first_page(self):
        result = paginate(list(range(50)), page=1, page_size=10)
        self.assertEqual(len(result["items"]), 10)
        self.assertEqual(result["total"], 50)

    def test_last_page_partial(self):
        result = paginate(list(range(15)), page=2, page_size=10)
        self.assertEqual(len(result["items"]), 5)


class TestValidateEmail(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(validate_email("user@example.com"))

    def test_invalid_no_at(self):
        self.assertFalse(validate_email("userexample.com"))

    def test_invalid_no_domain(self):
        self.assertFalse(validate_email("user@"))


class TestValidateRequiredFields(unittest.TestCase):
    def test_all_present(self):
        self.assertEqual(validate_required_fields({"a": 1, "b": 2}, ["a", "b"]), [])

    def test_missing_field(self):
        self.assertEqual(validate_required_fields({"a": 1}, ["a", "b"]), ["b"])


class TestPasswordStrength(unittest.TestCase):
    def test_valid_password(self):
        self.assertIsNone(validate_password_strength("Secure1pass"))

    def test_too_short(self):
        self.assertIn("at least", validate_password_strength("Ab1"))

    def test_no_digit(self):
        self.assertIn("digit", validate_password_strength("NoDigitsHere"))

    def test_no_uppercase(self):
        self.assertIn("uppercase", validate_password_strength("nouppercase1"))


if __name__ == "__main__":
    unittest.main()
