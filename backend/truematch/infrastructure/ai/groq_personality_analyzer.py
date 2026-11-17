"""Capa anticorrupción del proveedor de IA: respuesta de Groq → BigFiveProfile con evidencia verificada."""
from dataclasses import dataclass

from truematch.domain.creator_profiling.big_five import BigFiveProfile, TraitAssessment
from truematch.domain.creator_profiling.trait_evidence import verify_quotes

from .groq_client import GroqClient
from .json_extractor import extract_json
from .prompts import BRAND_CATEGORIES, LEGACY_TRAIT_KEYS, build_prompt, build_references


@dataclass(frozen=True)
class PersonalityAnalysis:
    big_five: BigFiveProfile
    communication_tone: str
    interests: tuple[str, ...]
    brand_affinity: tuple[dict, ...]   # [{"categoria", "motivo"}], como en el formato heredado
    analyzed_videos: int               # videos enviados a la IA (con referencia p1…pN)
    discarded_quotes: int              # citas que no aparecen literalmente o con referencia desconocida


def _claims(trait_data, ref_to_video):
    evidence = trait_data.get("evidencias") if isinstance(trait_data, dict) else None
    for item in evidence if isinstance(evidence, list) else []:
        if isinstance(item, dict):
            yield ref_to_video.get(str(item.get("ref", "")).strip()), item.get("cita")
        else:
            yield None, None


def parse_response(data, references):
    """Traduce el JSON de la IA aplicando las reglas del dominio. No hace llamadas de red."""
    if not isinstance(data, dict):
        raise ValueError("La respuesta de la IA no es un objeto JSON.")
    ref_to_video = {ref: video_id for ref, video_id, _ in references}
    descriptions = {video_id: text for _, video_id, text in references}
    traits_data = data.get("rasgos") if isinstance(data.get("rasgos"), dict) else {}

    assessments, discarded = [], 0
    for trait, key in LEGACY_TRAIT_KEYS.items():
        trait_data = traits_data.get(key)
        evidence, rejected = verify_quotes(_claims(trait_data, ref_to_video), descriptions)
        discarded += rejected
        raw_score = trait_data.get("puntaje") if isinstance(trait_data, dict) else None
        assessments.append(TraitAssessment.assess(trait, raw_score, evidence, len(references)))

    affinity = []
    for item in data.get("afinidad_marcas", []) if isinstance(data.get("afinidad_marcas"), list) else []:
        if isinstance(item, dict) and item.get("categoria") in BRAND_CATEGORIES:
            affinity.append({"categoria": item["categoria"], "motivo": str(item.get("motivo", "")).strip()})
    interests = data.get("intereses", [])
    if not isinstance(interests, list):
        interests = []

    return PersonalityAnalysis(
        big_five=BigFiveProfile(tuple(assessments), str(data.get("resumen", "")).strip()),
        communication_tone=str(data.get("tono_comunicacion", "")).strip(),
        interests=tuple(str(i).strip() for i in interests if str(i).strip())[:5],
        brand_affinity=tuple(affinity[:3]),
        analyzed_videos=len(references),
        discarded_quotes=discarded,
    )


class GroqPersonalityAnalyzer:
    def __init__(self, client: GroqClient):
        self.client = client

    def analyze(self, publications):
        """publications: [(video_id, descripción)] en orden. Devuelve PersonalityAnalysis."""
        references = build_references(publications)
        if not references:
            raise ValueError("El perfil no tiene descripciones de videos para analizar.")
        content = self.client.complete(build_prompt(references))
        return parse_response(extract_json(content), references)
