# -*- coding: utf-8 -*-
"""Тесты для функций calculate и load_params (Тема 2)."""

import os
import unittest
from main import calculate, load_params


class TestCalculate(unittest.TestCase):
    """Тесты для функции calculate."""

    def test_division_half(self):
        """Тест 1/2 с epsilon=0.01 → 0.5."""
        self.assertAlmostEqual(calculate(1, 2, epsilon=0.01), 0.5)

    def test_division_small(self):
        """Тест 1/1000 с epsilon=0.001 → 0.001."""
        self.assertAlmostEqual(calculate(1, 1000, epsilon=0.001), 0.001)

    def test_division_by_zero(self):
        """Деление на ноль вызывает ZeroDivisionError."""
        with self.assertRaises(ZeroDivisionError):
            calculate(10, 0)

    def test_epsilon_too_large(self):
        """epsilon >= 0.1 выходит за границу диапазона → ValueError."""
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=0.5)

    def test_epsilon_too_small(self):
        """epsilon <= 1e-9 выходит за границу диапазона → ValueError."""
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=1e-10)

    def test_epsilon_boundary_exact_tenth(self):
        """epsilon == 0.1 (граница) тоже должен быть отклонён."""
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=0.1)

    def test_float_operands(self):
        """Функция принимает дробные операнды."""
        result = calculate(2.5, 0.5, epsilon=0.01)
        self.assertAlmostEqual(result, 5.0)

    def test_epsilon_rounds_result(self):
        """Результат округляется в соответствии с epsilon."""
        # 1/3 ≈ 0.33333… при epsilon=0.01 → 0.33
        result = calculate(1, 3, epsilon=0.01)
        self.assertEqual(result, 0.33)


class TestLoadParams(unittest.TestCase):
    """Тесты для функции load_params."""

    def setUp(self):
        self.test_ini = "test_settings.ini"

    def tearDown(self):
        if os.path.exists(self.test_ini):
            os.remove(self.test_ini)

    def test_load_params_success(self):
        """Успешное чтение epsilon из корректного файла."""
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = 0.005\n")
        self.assertAlmostEqual(load_params(self.test_ini), 0.005)

    def test_file_not_found(self):
        """Отсутствующий файл вызывает FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_params("missing_file.ini")

    def test_bad_format(self):
        """Нечисловое значение epsilon вызывает ValueError."""
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = not_a_number\n")
        with self.assertRaises(ValueError):
            load_params(self.test_ini)

    def test_missing_section(self):
        """Отсутствие секции [Settings] вызывает KeyError."""
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[WrongSection]\nepsilon = 0.01\n")
        with self.assertRaises(KeyError):
            load_params(self.test_ini)

    def test_epsilon_in_valid_range(self):
        """Считанный epsilon попадает в допустимый диапазон."""
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = 0.005\n")
        eps = load_params(self.test_ini)
        self.assertTrue(1e-9 < eps < 0.1)


if __name__ == "__main__":
    unittest.main()
