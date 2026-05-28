# -*- coding: utf-8 -*-
"""
Лабораторная работа: Паттерн «Одиночка» (Singleton) — курсы валют ЦБ РФ

Singleton реализован через метакласс (Method 3).
Источник: https://stackoverflow.com/questions/6760685/

Структура модуля:
- ``float_to_parts`` — разбивает строковое значение курса на (целая, дробная) части.
- ``SingletonMeta`` — метакласс, гарантирующий единственность экземпляра.
- ``CurrencyFetcher`` — основной класс для получения и кэширования курсов валют.
"""

import os
import time
from datetime import datetime
from typing import Optional

import requests
import xml.etree.ElementTree as ET
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def float_to_parts(value_str: str) -> tuple:
    """
    Преобразует строку '113,2069' в кортеж ('113', '2069').

    Хранение float-значения отдельно — целая и дробная часть.
    См. https://digitology.tech/docs/python_3/tutorial/floatingpoint.html

    Args:
        value_str (str): Строковое представление числа, разделитель — запятая.

    Returns:
        tuple: Пара строк (целая_часть, дробная_часть).

    Example:
        >>> float_to_parts('113,2069')
        ('113', '2069')
        >>> float_to_parts('5')
        ('5', '0')
    """
    value_str = value_str.replace(",", ".")
    if "." in value_str:
        int_part, frac_part = value_str.split(".", 1)
    else:
        int_part, frac_part = value_str, "0"
    return (int_part, frac_part)


# ---------------------------------------------------------------------------
# Метакласс Singleton (Method 3)
# ---------------------------------------------------------------------------

class SingletonMeta(type):
    """
    Метакласс, реализующий паттерн «Одиночка».

    Гарантирует, что для каждого класса, использующего этот метакласс,
    существует не более одного экземпляра.
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        """Возвращает существующий экземпляр или создаёт новый."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


# ---------------------------------------------------------------------------
# Основной класс
# ---------------------------------------------------------------------------

class CurrencyFetcher(metaclass=SingletonMeta):
    """
    Получает и кэширует курсы валют с сайта ЦБ РФ.

    Принимает список ID валют (например, 'R01035' для GBP).
    Запрос к серверу выполняется не чаще одного раза в ``throttle_seconds``.

    Attributes:
        CBR_URL (str): URL XML-фида Центробанка РФ.

    Example:
        >>> fetcher = CurrencyFetcher(throttle_seconds=1.0)
        >>> fetcher2 = CurrencyFetcher()
        >>> fetcher is fetcher2
        True
    """

    CBR_URL: str = "http://www.cbr.ru/scripts/XML_daily.asp"

    def __init__(self, throttle_seconds: float = 1.0) -> None:
        """
        Инициализирует фетчер.

        Args:
            throttle_seconds (float): Минимальный интервал между запросами (сек.).
        """
        self.__throttle_seconds: float = throttle_seconds
        self.__last_request_time: float = 0.0
        # Кэш: ID валюты → словарь с данными
        self.__cache: dict = {}

    def __del__(self) -> None:
        """Деструктор: очищает кэш при удалении объекта."""
        self.__cache.clear()

    # ------------------------------------------------------------------
    # Геттеры и сеттеры
    # ------------------------------------------------------------------

    @property
    def throttle_seconds(self) -> float:
        """Минимальный интервал между запросами к серверу ЦБ РФ."""
        return self.__throttle_seconds

    @throttle_seconds.setter
    def throttle_seconds(self, value: float) -> None:
        """
        Устанавливает интервал троттлинга.

        Args:
            value (float): Новое значение интервала в секундах.

        Raises:
            ValueError: Если значение отрицательное.
        """
        if value < 0:
            raise ValueError("throttle_seconds не может быть отрицательным")
        self.__throttle_seconds = value

    # ------------------------------------------------------------------
    # Приватные методы
    # ------------------------------------------------------------------

    def __fetch_xml(self) -> Optional[ET.Element]:
        """
        Выполняет HTTP-запрос к ЦБ РФ и возвращает корневой элемент XML.

        Returns:
            Optional[ET.Element]: Корневой элемент или None при ошибке.
        """
        try:
            response = requests.get(self.CBR_URL, timeout=10)
            # ET сам читает кодировку windows-1251 из XML-заголовка
            return ET.fromstring(response.content)
        except requests.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None
        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return None

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    def get_currencies(self, currencies_ids_lst: list) -> list:
        """
        Возвращает курсы валют по списку ID ЦБ РФ.

        Данные обновляются не чаще одного раза в ``throttle_seconds``.
        При повторном вызове раньше этого времени используется кэш.

        Args:
            currencies_ids_lst (list): Список ID, например ['R01035', 'R01335'].

        Returns:
            list: Список словарей вида::

                [{'GBP': ('Фунт стерлингов', ('113', '2069'))}, ...]

            Для неверного ID: ``[{'R9999': None}]``.

        Example:
            >>> fetcher = CurrencyFetcher()
            >>> result = fetcher.get_currencies(['R01035'])
            >>> isinstance(result, list)
            True
        """
        elapsed = time.time() - self.__last_request_time

        if not self.__cache or elapsed >= self.__throttle_seconds:
            if elapsed < self.__throttle_seconds:
                time.sleep(self.__throttle_seconds - elapsed)
            root = self.__fetch_xml()
            self.__last_request_time = time.time()
            if root is not None:
                self.__cache.clear()
                for valute in root.findall("Valute"):
                    vid = valute.get("ID", "").strip()
                    self.__cache[vid] = {
                        "charcode": valute.findtext("CharCode", "").strip(),
                        "name": valute.findtext("Name", "").strip(),
                        "nominal": int(valute.findtext("Nominal", "1").strip()),
                        "parts": float_to_parts(valute.findtext("Value", "0").strip()),
                    }

        result = []
        for vid in currencies_ids_lst:
            if vid in self.__cache:
                entry = self.__cache[vid]
                charcode = entry["charcode"]
                name = entry["name"]
                parts = entry["parts"]
                nominal = entry["nominal"]
                # Если номинал не 1, сохраняем его для корректного пересчёта
                if nominal != 1:
                    result.append({charcode: (name, parts, nominal)})
                else:
                    result.append({charcode: (name, parts)})
            else:
                result.append({vid: None})

        return result

    def plot_currencies(self, output_path: str = "currencies.jpg") -> None:
        """
        Строит горизонтальную диаграмму топ-15 валют по курсу и сохраняет в файл.

        Файл используется для вставки в README.md.

        Args:
            output_path (str): Путь для сохранения графика. По умолчанию 'currencies.jpg'.
        """
        if not self.__cache:
            self.get_currencies([])  # прогрев кэша

        items = sorted(
            self.__cache.items(),
            key=lambda x: float(f"{x[1]['parts'][0]}.{x[1]['parts'][1]}"),
            reverse=True,
        )[:15]

        codes = [v["charcode"] for _, v in items]
        values = [float(f"{v['parts'][0]}.{v['parts'][1]}") for _, v in items]
        names = [v["name"][:22] for _, v in items]

        fig, ax = plt.subplots(figsize=(12, 6))
        colors = plt.cm.viridis([i / len(codes) for i in range(len(codes))])
        bars = ax.barh(codes, values, color=colors)

        for bar, val, name in zip(bars, values, names):
            ax.text(
                bar.get_width() + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.4f} ₽  ({name})",
                va="center",
                ha="left",
                fontsize=8,
            )

        ax.set_xlabel("Курс к рублю (₽)")
        ax.set_title(
            f"Курсы валют ЦБ РФ на {datetime.now().strftime('%d.%m.%Y')}",
            fontweight="bold",
        )
        ax.invert_yaxis()
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"График сохранён: {output_path}")


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fetcher = CurrencyFetcher(throttle_seconds=1.0)
    fetcher2 = CurrencyFetcher()

    print(f"fetcher is fetcher2: {fetcher is fetcher2}")  # True

    print("\nКурсы GBP, KZT, TRY:")
    results = fetcher.get_currencies(["R01035", "R01335", "R01700J"])
    for item in results:
        for code, val in item.items():
            if val:
                print(f"  {code}: {val[0]} — {val[1][0]},{val[1][1]}")

    print("\nНеверный ID:")
    print(fetcher.get_currencies(["R9999"]))

    print("\nСтроим график...")
    chart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "currencies.jpg")
    fetcher.plot_currencies(output_path=chart_path)
