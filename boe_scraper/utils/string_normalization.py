import re
import unicodedata


def to_snake_no_accents(text: str) -> str:
    # Normalize and remove accents
    normalized = unicodedata.normalize("NFD", text)
    no_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Lowercase
    no_accents = no_accents.lower()
    # Replace non-alphanumeric with underscores
    text_snake = re.sub(r"[^0-9a-z]+", "_", no_accents)
    # Strip leading/trailing underscores and collapse multiples
    text_snake = re.sub(r"_+", "_", text_snake).strip("_")
    return text_snake


def parse_euro_amount(amount_str: str) -> float:
    # Remove currency symbol and spaces
    cleaned = amount_str.strip()
    cleaned = re.sub(r"[^\d.,-]", "", cleaned)  # keep digits, . , -
    # Remove thousands separators (.)
    cleaned = cleaned.replace(".", "")
    # Convert decimal comma to dot
    cleaned = cleaned.replace(",", ".")
    return float(cleaned)
