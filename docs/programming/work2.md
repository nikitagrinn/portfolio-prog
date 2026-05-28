# Решение задачи деления с использованием конфигурационного файла

## Цель работы

Разработать программу на языке Python, которая:

1. Выполняет деление двух чисел с заданной точностью.
2. Загружает значение точности из конфигурационного файла.
3. Выполняет обработку ошибок через исключения.
4. Использует модульное тестирование для проверки корректности работы.

---

## Постановка задачи

### Задание

1. Написать функцию `calculate`, которая:

   * принимает два операнда и параметр точности `epsilon`;
   * **округляет результат** деления до числа знаков, соответствующего `epsilon`;
   * бросает `ZeroDivisionError` при делении на ноль;
   * бросает `ValueError` если `epsilon` вне допустимого диапазона.

   Допустимый диапазон значений:

   ```text
   10^-9 < epsilon < 10^-1
   ```

2. Написать функцию `load_params`, которая:

   * считывает значение `epsilon` из файла `settings.ini`;
   * бросает `FileNotFoundError` если файл не найден;
   * бросает `KeyError` если отсутствует секция или ключ;
   * бросает `ValueError` если значение epsilon не является числом.

3. Реализовать тестирование:

   Для функции `calculate`:

   * деление 1/2 и 1/1000;
   * деление на ноль;
   * epsilon вне допустимого диапазона;
   * проверка, что результат действительно округлён.

   Для функции `load_params`:

   * успешное чтение из файла;
   * отсутствие файла;
   * неверный формат числа;
   * отсутствие секции;
   * epsilon входит в допустимый диапазон.

---

## Описание решения

Программа состоит из следующих частей:

1. Функция `calculate` — выполняет деление и применяет `epsilon` для округления результата.
2. Функция `load_params` — загружает `epsilon` из конфигурационного файла.
3. Конфигурационный файл `settings.ini` — хранит значение `epsilon`.
4. Набор модульных тестов `test_app.py`.

### Как работает округление

Значение `epsilon` определяет нужную точность. Например, при `epsilon = 0.001` результат округляется до 3 знаков после запятой:

```
ndigits = -int(floor(log10(epsilon)))
# epsilon=0.001 → log10=-3 → ndigits=3
result = round(1/3, 3)  # → 0.333
```

---

## Листинг программы

### Файл `main.py`

```python
import configparser
import math
import os


def calculate(operand1: float, operand2: float, epsilon: float = 0.0001) -> float:
    """
    Делит operand1 на operand2 с учётом точности epsilon.

    Результат округляется до числа знаков, соответствующего epsilon.

    Args:
        operand1 (float): Делимое.
        operand2 (float): Делитель.
        epsilon (float): Точность. Допустимый диапазон: (1e-9, 0.1).

    Returns:
        float: Результат деления, округлённый до точности epsilon.

    Raises:
        ValueError: Если epsilon вне диапазона (1e-9, 1e-1).
        ZeroDivisionError: Если operand2 == 0.
    """
    if not (1e-9 < epsilon < 0.1):
        raise ValueError("Точность (epsilon) вне допустимого диапазона (1e-9, 1e-1).")

    if operand2 == 0:
        raise ZeroDivisionError("Деление на ноль невозможно.")

    result = float(operand1) / float(operand2)
    ndigits = -int(math.floor(math.log10(epsilon)))
    return round(result, ndigits)


def load_params(config_file: str = "settings.ini") -> float:
    """
    Считывает значение epsilon из секции [Settings] файла .ini.

    Args:
        config_file (str): Путь к файлу конфигурации.

    Returns:
        float: Значение epsilon.

    Raises:
        FileNotFoundError: Если файл не найден.
        KeyError: Если нет секции [Settings] или ключа epsilon.
        ValueError: Если значение не является числом.
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Файл {config_file} не найден.")

    config = configparser.ConfigParser()
    config.read(config_file, encoding="utf-8")

    try:
        return config.getfloat("Settings", "epsilon")
    except (configparser.NoSectionError, configparser.NoOptionError):
        raise KeyError("Секция [Settings] или ключ 'epsilon' не найдены.")
    except ValueError:
        raise ValueError("Неверный формат числа в файле конфигурации.")


if __name__ == "__main__":
    eps = load_params("settings.ini")
    print(f"Считана точность из файла: epsilon = {eps}")

    result = calculate(1, 3, epsilon=eps)
    print(f"1 / 3 с точностью {eps}: {result}")
```

---

### Конфигурационный файл `settings.ini`

```ini
[Settings]
epsilon = 0.00005
```

---

### Файл `test_app.py`

```python
import os
import unittest
from main import calculate, load_params


class TestCalculate(unittest.TestCase):

    def test_division_half(self):
        """Тест 1/2 с epsilon=0.01 → 0.5."""
        self.assertAlmostEqual(calculate(1, 2, epsilon=0.01), 0.5)

    def test_division_small(self):
        """Тест 1/1000 с epsilon=0.001 → 0.001."""
        self.assertAlmostEqual(calculate(1, 1000, epsilon=0.001), 0.001)

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            calculate(10, 0)

    def test_epsilon_too_large(self):
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=0.5)

    def test_epsilon_too_small(self):
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=1e-10)

    def test_epsilon_boundary_exact_tenth(self):
        """epsilon == 0.1 (граница) тоже должен быть отклонён."""
        with self.assertRaises(ValueError):
            calculate(1, 2, epsilon=0.1)

    def test_float_operands(self):
        result = calculate(2.5, 0.5, epsilon=0.01)
        self.assertAlmostEqual(result, 5.0)

    def test_epsilon_rounds_result(self):
        """1/3 при epsilon=0.01 → 0.33."""
        result = calculate(1, 3, epsilon=0.01)
        self.assertEqual(result, 0.33)


class TestLoadParams(unittest.TestCase):

    def setUp(self):
        self.test_ini = "test_settings.ini"

    def tearDown(self):
        if os.path.exists(self.test_ini):
            os.remove(self.test_ini)

    def test_load_params_success(self):
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = 0.005\n")
        self.assertAlmostEqual(load_params(self.test_ini), 0.005)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_params("missing_file.ini")

    def test_bad_format(self):
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = not_a_number\n")
        with self.assertRaises(ValueError):
            load_params(self.test_ini)

    def test_missing_section(self):
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[WrongSection]\nepsilon = 0.01\n")
        with self.assertRaises(KeyError):
            load_params(self.test_ini)

    def test_epsilon_in_valid_range(self):
        with open(self.test_ini, "w", encoding="utf-8") as f:
            f.write("[Settings]\nepsilon = 0.005\n")
        eps = load_params(self.test_ini)
        self.assertTrue(1e-9 < eps < 0.1)


if __name__ == "__main__":
    unittest.main()
```

---

## Результаты тестирования

| № | Тест | Проверка | Результат |
|---|------|----------|-----------|
| 1 | `test_division_half` | Деление 1/2 → 0.5 | ✅ OK |
| 2 | `test_division_small` | Деление 1/1000 → 0.001 | ✅ OK |
| 3 | `test_division_by_zero` | Деление на ноль → `ZeroDivisionError` | ✅ OK |
| 4 | `test_epsilon_too_large` | epsilon=0.5 → `ValueError` | ✅ OK |
| 5 | `test_epsilon_too_small` | epsilon=1e-10 → `ValueError` | ✅ OK |
| 6 | `test_epsilon_boundary_exact_tenth` | epsilon=0.1 (граница) → `ValueError` | ✅ OK |
| 7 | `test_float_operands` | Дробные операнды | ✅ OK |
| 8 | `test_epsilon_rounds_result` | 1/3 при eps=0.01 → 0.33 | ✅ OK |
| 9 | `test_load_params_success` | Успешное чтение epsilon | ✅ OK |
| 10 | `test_file_not_found` | Файл не найден → `FileNotFoundError` | ✅ OK |
| 11 | `test_bad_format` | Нечисловой epsilon → `ValueError` | ✅ OK |
| 12 | `test_missing_section` | Нет `[Settings]` → `KeyError` | ✅ OK |
| 13 | `test_epsilon_in_valid_range` | Считанный epsilon в допустимом диапазоне | ✅ OK |

```
Ran 13 tests in 0.002s

OK
```

---

## Используемые библиотеки

| Библиотека | Назначение |
|---|---|
| `configparser` | Работа с `.ini`-файлами |
| `math` | Вычисление количества знаков округления |
| `os` | Проверка существования файла |
| `unittest` | Модульное тестирование |

---

## Структура файлов

```
├── main.py            # Основные функции
├── settings.ini       # Конфигурационный файл с epsilon
└── test_app.py        # Модульные тесты
```

---

## Вывод

В ходе выполнения работы была разработана программа для деления чисел с параметром точности `epsilon`, загружаемым из конфигурационного файла `settings.ini`.

В программе реализованы:

* деление с проверкой входных данных и **округлением** результата по значению `epsilon`;
* корректная обработка ошибок (`ValueError`, `ZeroDivisionError`, `FileNotFoundError`, `KeyError`);
* загрузка параметров из `.ini`-файла;
* 13 модульных тестов, покрывающих основные и граничные случаи.

---

## 📁 Файлы проекта

| Файл | Описание |
|---|---|
| [main.py](lab2/main.py) | Функции `calculate` и `load_params` |
| [settings.ini](lab2/settings.ini) | Конфигурационный файл с epsilon |
| [test_app.py](lab2/test_app.py) | Модульные тесты |
