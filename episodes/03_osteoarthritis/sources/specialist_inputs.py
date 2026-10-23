"""Strict, bounded capture helpers. A missing signal never becomes a measurement."""
import math
import unicodedata


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', str(value or '').lower())
                   if unicodedata.category(c) != 'Mn').strip()


def number(data, key, low, high, *, optional=False):
    value = data.get(key)
    if optional and value in (None, ''):
        return None
    if isinstance(value, bool):
        raise ValueError(key)
    try:
        value = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(key) from None
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(key)
    return value


def text(data, key, *, optional=False, limit=600):
    value = data.get(key)
    if optional and value in (None, ''):
        return ''
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise ValueError(key)
    return value.strip()


def choice(data, key, options):
    value = normalized(data.get(key))
    if value not in options:
        raise ValueError(key)
    return value


def yes_no(data, key):
    if isinstance(data.get(key), bool):
        return data[key]
    value = choice(data, key, {'si', 'no'})
    return value == 'si'

