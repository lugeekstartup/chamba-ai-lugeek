"""
CV Parser and Ingestion Engine using OpenAI Structured Outputs.
Extracts structured facts, immutable technical skill years, education, and certifications from PDF CVs.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class ExtractedSkill(BaseModel):
    name: str = Field(description="Nombre de la tecnología o habilidad técnica")
    years_experience: float = Field(description="Años calculados de experiencia demostrable")
    proficiency: str = Field(default="Intermediate", description="Nivel: Junior, Intermediate, Advanced, Expert")


class LanguageSkill(BaseModel):
    language: str = Field(description="Nombre del idioma, ej: Español, Inglés")
    proficiency: str = Field(description="Nivel de dominio, ej: Nativo, C1, B2, Intermedio")


class FactSkill(BaseModel):
    skill_name: str = Field(description="Nombre de la tecnología o herramienta, ej: python, postgresql, docker")
    years_experience: float = Field(description="Años reales acumulados")


class WorkExperience(BaseModel):
    company: str
    title: str
    duration_years: float
    technologies_used: List[str]
    responsibilities_summary: str


class ParsedCandidateProfile(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline_or_role: str
    total_years_experience: float
    skills_with_years: List[ExtractedSkill]
    work_history: List[WorkExperience]
    education: List[str] = Field(default_factory=list, description="Títulos universitarios, grados académicos, maestrías o instituciones")
    certifications: List[str] = Field(default_factory=list, description="Certificaciones profesionales, diplomas, licencias o acreditaciones")
    languages: List[LanguageSkill] = Field(default_factory=list, description="Idiomas y nivel de dominio")
    fact_sheet_skills: List[FactSkill] = Field(default_factory=list, description="Habilidades con años de experiencia calculados")


class CVParser:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key no configurada. Por favor, ingrésala en la sección de Configuración de IA de la aplicación.")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if self.base_url and not self.base_url.strip():
            self.base_url = None
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts plain text from all pages of a PDF CV."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Archivo CV no encontrado en: {pdf_path}")
        
        reader = PdfReader(pdf_path)
        extracted_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        return "\n".join(extracted_text)

    def parse_cv_to_structured_profile(self, raw_text: str) -> ParsedCandidateProfile:
        """Uses AI with structured output to parse CV details."""
        system_prompt = (
            "Eres un experto en reclutamiento técnico, ATS y análisis curricular. "
            "Tu tarea es analizar el texto extraído del CV de un candidato y generar una estructura de datos fidedigna y exhaustiva.\n"
            "Reglas:\n"
            "1. En 'fact_sheet_skills' y 'skills_with_years', calcula con precisión los años reales acumulados para cada lenguaje, framework, base de datos y herramienta técnica.\n"
            "2. En 'education', extrae todos los títulos profesionales, licenciaturas, maestrías y diplomados con su universidad o institución y año.\n"
            "3. En 'certifications', extrae certificaciones oficiales, diplomas y licencias relevantes. Si no tiene, retorna una lista vacía.\n"
            "4. En 'languages', extrae idiomas y niveles de dominio.\n"
            "5. NO inventes información. Basa todo estrictamente en el texto del CV."
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto del CV a analizar:\n\n{raw_text}"}
                ],
                response_format=ParsedCandidateProfile
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            # Fallback para gateways y endpoints compatibles (Luna 6, proxies locales, etc.)
            json_prompt = (
                f"{system_prompt}\n\n"
                "IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido con este esquema exacto:\n"
                f"{json.dumps(ParsedCandidateProfile.model_json_schema(), ensure_ascii=False)}"
            )
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": json_prompt},
                    {"role": "user", "content": f"Texto del CV a analizar:\n\n{raw_text}"}
                ]
            )
            raw_content = resp.choices[0].message.content or "{}"
            # Limpiar bloques markdown si existen
            raw_content = re.sub(r"^```json\s*", "", raw_content.strip())
            raw_content = re.sub(r"```$", "", raw_content.strip())
            data = json.loads(raw_content)
            return ParsedCandidateProfile.model_validate(data)

    def generate_embedding(self, profile_summary_text: str) -> List[float]:
        """Generates a 1536-dim embedding vector using text-embedding-3-small."""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=profile_summary_text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[Warning] No se pudo generar embedding vectorial: {e}")
            return []

    def process_cv_file(self, pdf_path: str, output_json_path: Optional[str] = None) -> Dict[str, Any]:
        """End-to-end processing: PDF -> Raw Text -> Structured Profile + Vector Embedding."""
        raw_text = self.extract_text_from_pdf(pdf_path)
        structured_profile = self.parse_cv_to_structured_profile(raw_text)
        
        # Build dense text representation for semantic embedding
        summary_for_vector = (
            f"Cargo: {structured_profile.headline_or_role}. "
            f"Años totales: {structured_profile.total_years_experience}. "
            f"Habilidades: {', '.join([s.name for s in structured_profile.skills_with_years])}. "
            f"Idiomas: {', '.join([f'{l.language} ({l.proficiency})' for l in structured_profile.languages])}. "
            f"Resumen: {' '.join([w.responsibilities_summary for w in structured_profile.work_history[:3]])}"
        )
        embedding = self.generate_embedding(summary_for_vector)

        # Standardize output for Web UI
        profile_dict = structured_profile.model_dump()
        profile_dict["skills_inventory"] = profile_dict.get("skills_with_years", [])
        profile_dict["professional_summary"] = profile_dict.get("headline_or_role", "")
        profile_dict["fact_sheet_skills"] = {
            s.skill_name.lower(): s.years_experience for s in structured_profile.fact_sheet_skills
        }
        profile_dict["languages_map"] = {
            l.language: l.proficiency for l in structured_profile.languages
        }
        profile_dict["languages"] = [
            f"{l.language} ({l.proficiency})" if l.proficiency else l.language for l in structured_profile.languages
        ]
        profile_dict["education"] = profile_dict.get("education", [])
        profile_dict["certifications"] = profile_dict.get("certifications", [])

        result = {
            "structured_profile": profile_dict,
            "embedding": embedding,
            "raw_text_length": len(raw_text)
        }

        if output_json_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        return result
