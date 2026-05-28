# -*- coding: utf-8 -*-
"""
Лабораторная работа 2. Деление с заданной точностью.

Модуль содержит:
- ``calculate`` — деление с валидацией и применением точности epsilon.
- ``load_params`` — считывание epsilon из конфигурационного файла .ini.
"""

import configparser
import math
import os


def calculate(operand1: float, operand2: float, epsilon: float = 0.0001) -> float:
    """
    Делит ``operand1`` на ``operand2`` с учётом точности ``epsilon``.

    Результат округляется до числа знаков после запятой,
    соответствующего значению epsilon (например, 0.001 → 3 знака).

    Args:
        operand1 (float): Делимое (целое или дробное).
        operand2 (float): Делитель (целое или дробное).
        epsilon (float): Точность результата. Допустимый диапазон: (1e-9, 0.1).

    Returns:
        float: Результат деления, округлённый до точности epsilon.

    Raises:
        ValueError: Если epsilon вне допустимого диапазона (1e-9, 1e-1).
        ZeroDivisionError: Если operand2 равен нулю.

    Example:
        >>> calculate(1, 2, epsilon=0.01)
        0.5
        >>> calculate(1, 1000, epsilon=0.001)
        0.001
    """
    if not (1e-9 < epsilon < 0.1):
        raise ValueError("Точность (epsilon) вне допустимого диапазона (1e-9, 1e-1).")

    if operand2 == 0:
        raise ZeroDivisionError("Деление на ноль невозможно.")

    result = float(operand1) / float(operand2)

    # Округляем результат до числа знаков, соответствующего epsilon.
    # Например: epsilon=0.001 → log10=−3 → ndigits=3
    ndigits = -int(math.floor(math.log10(epsilon)))
    return round(result, ndigits)


def load_params(config_file: str = "settings.ini") -> float:
    """
    Считывает значение точности epsilon из секции [Settings] файла .ini.

    Args:
        config_file (str): Путь к конфигурационному файлу. По умолчанию 'settings.ini'.

    Returns:
        float: Значение epsilon из файла конфигурации.

    Raises:
        FileNotFoundError: Если файл не найден.
        KeyError: Если секция [Settings] или ключ 'epsilon' отсутствуют.
        ValueError: Если значение epsilon не является числом.

    Example:
        >>> load_params('settings.ini')
        5e-05
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
    # Демонстрация связи load_params → calculate
    eps = load_params("settings.ini")
    print(f"Считана точность из файла: epsilon = {eps}")

    result = calculate(1, 3, epsilon=eps)
    print(f"1 / 3 с точностью {eps}: {result}")

    result2 = calculate(1, 2, epsilon=0.01)
    print(f"1 / 2 с точностью 0.01: {result2}")
