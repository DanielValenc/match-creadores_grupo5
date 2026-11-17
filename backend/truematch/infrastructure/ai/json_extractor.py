"""Extrae el objeto JSON de la respuesta del modelo."""
import json
import re


def extract_json(text):
    """Obtiene el objeto JSON de la respuesta, ignorando bloques <think> y markdown."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("La respuesta de la IA no contiene un JSON.")
    return json.loads(text[start:end + 1])
