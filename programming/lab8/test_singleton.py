# -*- coding: utf-8 -*-
"""
Тесты для модуля singleton_currencies.

Содержит:
- ``TestFloatToParts`` — юнит-тесты для вспомогательной функции.
- ``TestCurrencyFetcherUnit`` — мок-тесты для CurrencyFetcher (без сети).
- ``TestCurrencyFetcherIntegration`` — интеграционные тесты с реальным API ЦБ РФ.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from singleton_currencies import CurrencyFetcher, SingletonMeta, float_to_parts


# ---------------------------------------------------------------------------
# Вспомогательная XML-заглушка
# ---------------------------------------------------------------------------

_FAKE_XML_STR = """<?xml version="1.0" encoding="UTF-8"?>
<ValCurs Date="28.05.2026" name="Foreign Currency Market">
  <Valute ID="R01035">
    <NumCode>826</NumCode>
    <CharCode>GBP</CharCode>
    <Nominal>1</Nominal>
    <Name>Фунт стерлингов Соединённого королевства</Name>
    <Value>113,2069</Value>
    <VunitRate>113,2069</VunitRate>
  </Valute>
  <Valute ID="R01239">
    <NumCode>978</NumCode>
    <CharCode>EUR</CharCode>
    <Nominal>1</Nominal>
    <Name>Евро</Name>
    <Value>98,7654</Value>
    <VunitRate>98,7654</VunitRate>
  </Valute>
  <Valute ID="R01700J">
    <NumCode>949</NumCode>
    <CharCode>TRY</CharCode>
    <Nominal>10</Nominal>
    <Name>Турецких лир</Name>
    <Value>33,1224</Value>
    <VunitRate>3,31224</VunitRate>
  </Valute>
</ValCurs>
"""
# bytes для передачи в mock (ET.fromstring принимает bytes)
FAKE_XML: bytes = _FAKE_XML_STR.encode("utf-8")


# ---------------------------------------------------------------------------
# Тесты float_to_parts
# ---------------------------------------------------------------------------

class TestFloatToParts(unittest.TestCase):
    """Юнит-тесты для функции float_to_parts."""

    def test_comma_separator(self):
        """Строка с запятой корректно разбивается."""
        self.assertEqual(float_to_parts("113,2069"), ("113", "2069"))

    def test_no_decimal(self):
        """Целое число → дробная часть равна '0'."""
        self.assertEqual(float_to_parts("5"), ("5", "0"))

    def test_dot_separator(self):
        """Строка с точкой тоже обрабатывается корректно."""
        self.assertEqual(float_to_parts("98.765"), ("98", "765"))


# ---------------------------------------------------------------------------
# Мок-тесты (без реальной сети)
# ---------------------------------------------------------------------------

class TestCurrencyFetcherUnit(unittest.TestCase):
    """Юнит-тесты CurrencyFetcher с подменой сетевого слоя."""

    def _make_fetcher_with_cache(self) -> CurrencyFetcher:
        """Создаёт фетчер и принудительно заполняет кэш через мок."""
        # Сбрасываем синглтон перед каждым юнит-тестом
        SingletonMeta._instances.clear()
        fetcher = CurrencyFetcher(throttle_seconds=0)

        with patch("singleton_currencies.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = FAKE_XML
            mock_get.return_value = mock_resp
            fetcher.get_currencies([])  # прогрев кэша

        return fetcher

    def test_singleton_same_object(self):
        """Два вызова конструктора возвращают один и тот же объект."""
        SingletonMeta._instances.clear()
        f1 = CurrencyFetcher()
        f2 = CurrencyFetcher()
        self.assertIs(f1, f2)

    def test_invalid_id_returns_none(self):
        """Неверный ID → словарь {id: None}."""
        fetcher = self._make_fetcher_with_cache()
        result = fetcher.get_currencies(["R9999"])
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0].get("R9999"))

    def test_gbp_name_contains_russian(self):
        """Название GBP содержит русское слово 'Фунт'."""
        fetcher = self._make_fetcher_with_cache()
        result = fetcher.get_currencies(["R01035"])
        entry = result[0].get("GBP")
        self.assertIsNotNone(entry)
        self.assertIn("Фунт", entry[0])

    def test_gbp_value_in_range(self):
        """Курс GBP находится в диапазоне 0–999."""
        fetcher = self._make_fetcher_with_cache()
        result = fetcher.get_currencies(["R01035"])
        parts = result[0]["GBP"][1]
        val = float(f"{parts[0]}.{parts[1]}")
        self.assertGreater(val, 0)
        self.assertLess(val, 999)

    def test_parts_is_tuple_of_two_strings(self):
        """Значение курса хранится как кортеж из двух строк."""
        fetcher = self._make_fetcher_with_cache()
        result = fetcher.get_currencies(["R01035"])
        parts = result[0]["GBP"][1]
        self.assertIsInstance(parts, tuple)
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].isdigit())

    def test_nominal_not_one_stored(self):
        """Если номинал != 1, он сохраняется в результате."""
        fetcher = self._make_fetcher_with_cache()
        result = fetcher.get_currencies(["R01700J"])
        entry = result[0].get("TRY")
        self.assertIsNotNone(entry)
        # entry: (name, parts, nominal)
        self.assertEqual(len(entry), 3)
        self.assertEqual(entry[2], 10)

    def test_getter_setter_throttle(self):
        """Геттер и сеттер throttle_seconds работают корректно."""
        SingletonMeta._instances.clear()
        f = CurrencyFetcher()
        f.throttle_seconds = 2.5
        self.assertEqual(f.throttle_seconds, 2.5)

    def test_negative_throttle_raises(self):
        """Отрицательный throttle вызывает ValueError."""
        SingletonMeta._instances.clear()
        f = CurrencyFetcher()
        with self.assertRaises(ValueError):
            f.throttle_seconds = -1.0


# ---------------------------------------------------------------------------
# Интеграционные тесты (реальный API ЦБ РФ)
# ---------------------------------------------------------------------------

class TestCurrencyFetcherIntegration(unittest.TestCase):
    """
    Интеграционные тесты — требуют подключения к интернету.

    Запускайте отдельно: python -m pytest test_singleton.py -k Integration -v
    """

    @classmethod
    def setUpClass(cls):
        """Однократная загрузка данных для всех интеграционных тестов."""
        SingletonMeta._instances.clear()
        cls.fetcher = CurrencyFetcher(throttle_seconds=1.0)
        for attempt in range(3):
            result = cls.fetcher.get_currencies(["R01035"])
            if result and result[0].get("GBP") is not None:
                break
            cls.fetcher._CurrencyFetcher__last_request_time = 0
            time.sleep(1)
        else:
            raise RuntimeError("Не удалось получить данные с ЦБ РФ за 3 попытки")

    def test_invalid_id_real(self):
        """Неверный ID возвращает {id: None} (реальный запрос)."""
        result = self.fetcher.get_currencies(["R9999"])
        self.assertIsNone(result[0].get("R9999"))

    def test_gbp_name_russian_real(self):
        """Название GBP содержит 'Фунт' (реальный запрос)."""
        result = self.fetcher.get_currencies(["R01035"])
        entry = result[0].get("GBP")
        self.assertIsNotNone(entry)
        self.assertIn("Фунт", entry[0])

    def test_gbp_value_range_real(self):
        """Курс GBP в диапазоне 0–999 (реальный запрос)."""
        result = self.fetcher.get_currencies(["R01035"])
        parts = result[0]["GBP"][1]
        val = float(f"{parts[0]}.{parts[1]}")
        self.assertGreater(val, 0)
        self.assertLess(val, 999)


if __name__ == "__main__":
    # Запуск только юнит-тестов (без сети)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestFloatToParts))
    suite.addTests(loader.loadTestsFromTestCase(TestCurrencyFetcherUnit))
    unittest.TextTestRunner(verbosity=2).run(suite)
