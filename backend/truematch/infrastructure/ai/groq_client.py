"""Cliente HTTP mínimo de Groq (API compatible con OpenAI): chat completions y lista de modelos."""
import requests

from truematch.infrastructure.config import DEFAULT_GROQ_MODEL as DEFAULT_MODEL

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS_URL = "https://api.groq.com/openai/v1/models"
SYSTEM_MESSAGE = "You output only valid JSON without markdown formatting."


class GroqError(RuntimeError):
    """No se obtuvo una respuesta usable de Groq."""


class GroqClient:
    def __init__(self, api_key, model=DEFAULT_MODEL, timeout=60, temperature=0.3):
        if not api_key:
            raise GroqError("Falta GROQ_API_KEY.")
        self.api_key, self.model, self.timeout, self.temperature = api_key, model, timeout, temperature

    def complete(self, prompt):
        """Envía el prompt y devuelve el texto de la respuesta."""
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
        }
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as error:
            raise GroqError(f"Error de conexión con la API: {error}") from None
        if response.status_code != 200:
            raise GroqError(f"Error en la API. Código: {response.status_code}\n{response.text}")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError):
            raise GroqError("La respuesta de Groq no tiene el formato esperado.") from None

    def list_models(self):
        """IDs de los modelos a los que tiene acceso la cuenta, ordenados (antes listar_modelos)."""
        try:
            response = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {self.api_key}"},
                                    timeout=30)
            response.raise_for_status()
            return sorted(item["id"] for item in response.json().get("data", []))
        except requests.RequestException as error:
            raise GroqError(f"No se pudo obtener la lista de modelos: {error}") from None
        except (KeyError, TypeError, ValueError):
            raise GroqError("La lista de modelos de Groq no tiene el formato esperado.") from None
