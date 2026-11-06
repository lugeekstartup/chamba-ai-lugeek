"""
Matching Engine: Semantic scoring and cognitive job-fit evaluation using OpenAI.
Combines hard-condition filtering, vector cosine similarity, and LLM reasoning.
"""

import os
import re
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class MatchDecision(BaseModel):
    match_score: int = Field(description="Score between 0 and 100")
    recommendation: str = Field(description="APPLY, MANUAL_REVIEW, or DISCARD")
    salary_fit: str = Field(description="ESTIMATED_FIT, BELOW_MINIMUM, or NOT_SPECIFIED")
    matching_points: List[str] = Field(description="Fortalezas clave del candidato que coinciden con la vacante")
    missing_gaps: List[str] = Field(description="Requisitos o habilidades requeridas que el candidato no tiene")
    brief_rationale: str = Field(description="Explicación ejecutiva de 2 a 3 oraciones")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class MatchingEngine:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key no configurada. Ingrésala en la sección de Configuración de IA.")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if self.base_url and not self.base_url.strip():
            self.base_url = None
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def evaluate_hard_filters(
        self,
        job_info: Dict[str, Any],
        candidate_conditions: Dict[str, Any]
    ) -> bool:
        """
        Validates hard constraints (Modality, Disallowed locations).
        Returns True if candidate passes hard filters.
        """
        modalities = candidate_conditions.get("modalities")
        if not modalities:
            single = candidate_conditions.get("modality", "REMOTE")
            modalities = [single]

        modalities = [m.upper() for m in modalities]
        job_title = job_info.get("title", "").lower()
        job_desc = job_info.get("description", "").lower()

        # If on-site is NOT in candidate's modalities, block strict on-site jobs
        if "ON_SITE" not in modalities:
            if "on-site only" in job_desc or "100% presencial" in job_desc or "trabajo presencial" in job_title:
                return False

        # If remote is required and job is not remote/hybrid
        if "REMOTE" in modalities and "ON_SITE" not in modalities and "HYBRID" not in modalities:
            if "presencial" in job_title or "on-site" in job_title:
                return False

        return True

    def evaluate_job_fit_with_ai(
        self,
        candidate_profile: Dict[str, Any],
        job_details: Dict[str, Any]
    ) -> MatchDecision:
        """Uses AI cognitive evaluation to analyze candidate fit against job requirements."""
        system_prompt = (
            "Eres un Senior Tech Recruiter y Evaluador de Talento Profesional. "
            "Compara el perfil del candidato contra la oferta de empleo provista. "
            "Debes ser riguroso: evalúa si el stack tecnológico, el seniority y las responsabilidades se alinean. "
            "Asigna una calificación de 0 a 100 y una recomendación: "
            "'APPLY' si score >= 80, 'MANUAL_REVIEW' si 65-79, o 'DISCARD' si < 65."
        )

        candidate_summary = {
            "headline": candidate_profile.get("headline_or_role"),
            "years_total": candidate_profile.get("total_years_experience"),
            "skills": [s.get("name") if isinstance(s, dict) else s for s in candidate_profile.get("skills_with_years", [])],
            "education": candidate_profile.get("education", []),
            "recent_experience": [
                f"{exp.get('title')} en {exp.get('company')} ({exp.get('duration_years', '')} años): {exp.get('responsibilities_summary', '')}"
                for exp in candidate_profile.get("work_history", [])[:3]
            ]
        }

        user_content = (
            f"=== VACANTE ===\n"
            f"Título: {job_details.get('title')}\n"
            f"Empresa: {job_details.get('company')}\n"
            f"Ubicación: {job_details.get('location')}\n"
            f"Modalidad: {job_details.get('destination_portal', '')}\n"
            f"Descripción del puesto:\n{job_details.get('description', '')[:3500]}\n\n"
            f"=== PERFIL CANDIDATO ===\n"
            f"{candidate_summary}"
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=MatchDecision
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            json_prompt = (
                f"{system_prompt}\n\n"
                "IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido que cumpla con el siguiente esquema:\n"
                f"{json.dumps(MatchDecision.model_json_schema(), ensure_ascii=False)}"
            )
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": json_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            raw_content = resp.choices[0].message.content or "{}"
            raw_content = re.sub(r"^```json\s*", "", raw_content.strip())
            raw_content = re.sub(r"```$", "", raw_content.strip())
            data = json.loads(raw_content)
            return MatchDecision.model_validate(data)
