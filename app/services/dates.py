"""Fechas en español. El día de la semana siempre se calcula, nunca lo escribe el modelo."""
from datetime import date, timedelta
from typing import List

WEEKDAYS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def next_business_days(start: date, count: int) -> List[date]:
    days, current = [], start
    while len(days) < count:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days.append(current)
    return days


def format_day(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()]} {day.day} de {MONTHS[day.month - 1]} de {day.year}"


def format_slot(day: date, hour: int, minute: int = 0) -> str:
    suffix = "a. m." if hour < 12 else "p. m."
    return f"{WEEKDAYS[day.weekday()]} {day.day} de {MONTHS[day.month - 1]}, {hour % 12 or 12}:{minute:02d} {suffix}"
