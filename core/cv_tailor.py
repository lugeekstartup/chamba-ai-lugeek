"""
CV Tailor & ATS Optimizer Engine - Harvard Standard Edition.
Generates 100% monochrome black & white, Harvard-compliant ATS resumes,
guaranteed strictly <= 2 pages with AI keyword injection and Playwright PDF export.
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class TailoredSkillCategory(BaseModel):
    category_name: str = Field(description="Nombre de la categoría, ej: Lenguajes & Frameworks, Cloud & DevOps, Bases de Datos, Metodologías & Gestión")
    skills: List[str] = Field(description="Lista de tecnologías y competencias clave que coinciden con la vacante")


class TailoredExperienceItem(BaseModel):
    company: str = Field(description="Nombre de la empresa")
    location: Optional[str] = Field(default=None, description="Ciudad, País o Remoto")
    title: str = Field(description="Cargo desempeñado")
    duration: str = Field(description="Periodo, ej: Ene 2021 – Presente o 2020 – 2023")
    bullet_points: List[str] = Field(
        description="2 a 3 viñetas concisas con verbos de acción, logros cuantificables y palabras clave ATS de la vacante."
    )


class TailoredEducationItem(BaseModel):
    degree: str = Field(description="Título profesional, grado académico, maestría o especialidad")
    institution: str = Field(description="Universidad o instituto")
    duration: Optional[str] = Field(default=None, description="Año o periodo, ej: 2023 – 2024")
    location: Optional[str] = Field(default=None, description="Ciudad, País")


class TailoredCertificationItem(BaseModel):
    name: str = Field(description="Nombre de la certificación o diploma")
    issuer: Optional[str] = Field(default=None, description="Entidad emisora")
    year: Optional[str] = Field(default=None, description="Año de emisión")


class TailoredResume(BaseModel):
    full_name: str
    target_headline: str = Field(description="Titular profesional estratégico alineado exactamente con la vacante")
    email: str
    phone: str
    location: str
    linkedin_url: Optional[str] = None
    professional_summary: str = Field(
        description="Resumen profesional de 3 a 4 líneas de alto impacto con palabras clave exactas del puesto."
    )
    skill_categories: List[TailoredSkillCategory] = Field(
        description="3 a 4 categorías de competencias en formato Harvard (Lenguajes, Cloud, BD, Gestión)"
    )
    core_competencies: List[str] = Field(
        description="Lista plana de 10-15 palabras clave principales ATS para la previsualización web"
    )
    work_experience: List[TailoredExperienceItem] = Field(
        description="Máximo 3 a 4 experiencias laborales más relevantes del candidato para garantizar estrictamente <= 2 páginas"
    )
    education: List[TailoredEducationItem] = Field(
        description="Formación académica formal del candidato"
    )
    certifications: Optional[List[TailoredCertificationItem]] = Field(
        default=None,
        description="Certificaciones profesionales relevantes si las posee el candidato"
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Idiomas y nivel de dominio, ej: Español (Nativo), Inglés (Avanzado C1)"
    )


class CVTailor:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, output_dir: Optional[Path] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key no configurada. Ingrésala en la sección de Configuración de IA de la aplicación.")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        if self.base_url and not self.base_url.strip():
            self.base_url = None
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.output_dir = output_dir or (BASE_DIR / "data" / "tailored_resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tailor_cv_with_ai(
        self,
        candidate_data: Dict[str, Any],
        job_info: Dict[str, Any]
    ) -> TailoredResume:
        """Adapts candidate CV to match job requirements and ATS keywords using AI under Harvard rules."""
        system_prompt = (
            "Eres un Especialista Senior en Reclutamiento Ejecutivo y Optimización de CVs para ATS "
            "siguiendo rigurosamente el ESTÁNDAR HARVARD (Harvard Resume Standard).\n\n"
            "NORMAS Y DIRECTRICES OBLIGATORIAS:\n"
            "1. ESTÁNDAR HARVARD MONOCROMÁTICO: Todo el contenido debe ser sobrio, profesional y de máximo rigor. "
            "No inventes empresas, cargos ni títulos que el candidato no tenga. Adapta la narrativa técnica y logros "
            "reales del candidato para responder directamente a las exigencias de la oferta.\n"
            "2. LÍMITE ESTRICTO DE 2 PÁGINAS (CRÍTICO): El CV final bajo ninguna circunstancia debe superar las 2 páginas. "
            "Para asegurar este límite físico:\n"
            "   - Selecciona un MÁXIMO de 3 a 5 roles laborales más relevantes y recientes del candidato.\n"
            "   - Escribe un MÁXIMO de 2 a 3 viñetas concisas por rol (máximo 2 líneas por viñeta).\n"
            "   - Cada viñeta debe comenzar con un fuerte verbo de acción (ej: 'Diseñé', 'Lideré', 'Implementé', 'Optimizé') "
            "e integrar métricas reales y palabras clave ATS solicitadas por el empleador.\n"
            "3. CATEGORIZACIÓN DE HABILIDADES HARVARD: En 'skill_categories', agrupa todas las tecnologías en 3 o 4 categorías "
            "claras (ej: 'Lenguajes & Frameworks', 'Cloud & DevOps', 'Bases de Datos & Arquitectura', 'Metodologías & Herramientas'). "
            "Adicionalmente, llena 'core_competencies' con una lista plana de 10-15 palabras clave para la UI.\n"
            "4. EDUCACIÓN & CERTIFICACIONES: Estructura la formación con grado, institución, año y ubicación. "
            "Incluye certificaciones relevantes si el candidato cuenta con ellas.\n"
            "5. RESUMEN PROFESIONAL: Párrafo directo de 3 a 4 líneas que conecte la propuesta de valor del candidato con la vacante."
        )

        user_content = (
            f"=== VACANTE OBJETIVO ===\n"
            f"Título: {job_info.get('title')}\n"
            f"Empresa: {job_info.get('company')}\n"
            f"Ubicación: {job_info.get('location')}\n"
            f"Descripción y Requisitos:\n{job_info.get('description', '')[:4000]}\n\n"
            f"=== PERFIL BASE DEL CANDIDATO ===\n"
            f"Nombre: {candidate_data.get('full_name')}\n"
            f"Email: {candidate_data.get('email')}\n"
            f"Teléfono: {candidate_data.get('phone')}\n"
            f"Ubicación: {candidate_data.get('location')}\n"
            f"Titular: {candidate_data.get('headline_or_role')}\n"
            f"Experiencia laboral:\n{candidate_data.get('work_history')}\n"
            f"Habilidades:\n{candidate_data.get('skills_with_years') or candidate_data.get('skills_inventory')}\n"
            f"Educación:\n{candidate_data.get('education')}\n"
            f"Certificaciones:\n{candidate_data.get('certifications')}\n"
            f"Idiomas:\n{candidate_data.get('languages')}\n"
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=TailoredResume
            )
            return completion.choices[0].message.parsed
        except Exception as e:
            json_prompt = (
                f"{system_prompt}\n\n"
                "IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido que cumpla con el siguiente esquema:\n"
                f"{json.dumps(TailoredResume.model_json_schema(), ensure_ascii=False)}"
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
            return TailoredResume.model_validate(data)

    def render_html_template(self, resume: TailoredResume) -> str:
        """
        Generates 100% monochrome black Harvard Standard ATS HTML.
        Uses classic serif typography, solid black divider rules, clean uppercase titles,
        and categorized text skills. No colored pills or badges.
        """
        contact_parts = []
        if resume.location:
            contact_parts.append(resume.location)
        if resume.phone:
            contact_parts.append(resume.phone)
        if resume.email:
            contact_parts.append(resume.email)
        if resume.linkedin_url:
            clean_li = resume.linkedin_url.replace("https://", "").replace("http://", "").replace("www.", "")
            contact_parts.append(clean_li)
        contact_line = " • ".join(contact_parts)

        # Categorized skills (Harvard standard inline lines)
        categories_html = ""
        for cat in resume.skill_categories:
            skills_str = ", ".join(cat.skills)
            categories_html += f"""
            <div class="skill-row">
                <span class="skill-cat-label">{cat.category_name}:</span> {skills_str}
            </div>
            """

        # Work experience entries
        exp_html = ""
        for exp in resume.work_experience:
            bullets = "".join([f"<li>{bp}</li>" for bp in exp.bullet_points])
            exp_html += f"""
            <div class="exp-item">
                <div class="exp-line-top">
                    <span class="exp-company">{exp.company}</span>
                    <span class="exp-right">{exp.location or ''}</span>
                </div>
                <div class="exp-line-sub">
                    <span class="exp-title">{exp.title}</span>
                    <span class="exp-right">{exp.duration}</span>
                </div>
                <ul class="exp-bullets">
                    {bullets}
                </ul>
            </div>
            """

        # Education entries
        edu_html = ""
        for edu in resume.education:
            edu_html += f"""
            <div class="edu-item">
                <div class="exp-line-top">
                    <span class="exp-company">{edu.degree}</span>
                    <span class="exp-right">{edu.location or ''}</span>
                </div>
                <div class="exp-line-sub">
                    <span class="exp-title">{edu.institution}</span>
                    <span class="exp-right">{edu.duration or ''}</span>
                </div>
            </div>
            """

        # Certifications section
        cert_section = ""
        if resume.certifications and len(resume.certifications) > 0:
            cert_items = ""
            for c in resume.certifications:
                details = [c.issuer, c.year]
                detail_str = f" — {', '.join([d for d in details if d])}" if any(details) else ""
                cert_items += f"<li><strong>{c.name}</strong>{detail_str}</li>"
            cert_section = f"""
            <div class="harvard-section">
                <h2 class="harvard-section-title">Certificaciones & Especializaciones</h2>
                <ul class="harvard-simple-list">
                    {cert_items}
                </ul>
            </div>
            """

        # Languages section
        lang_section = ""
        if resume.languages and len(resume.languages) > 0:
            langs_str = " • ".join(resume.languages)
            lang_section = f"""
            <div class="harvard-section">
                <h2 class="harvard-section-title">Idiomas</h2>
                <div class="harvard-text">{langs_str}</div>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{resume.full_name} - CV ATS Harvard</title>
<style>
    @page {{
        size: letter;
        margin: 12mm 15mm 12mm 15mm;
    }}
    * {{
        box-sizing: border-box;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    body {{
        font-family: 'Times New Roman', Times, Georgia, Garamond, serif;
        color: #000000;
        background: #ffffff;
        font-size: 10pt;
        line-height: 1.32;
        margin: 0;
        padding: 0;
    }}
    .harvard-header {{
        text-align: center;
        margin-bottom: 7px;
    }}
    .harvard-name {{
        font-size: 18pt;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0 0 2px 0;
        color: #000000;
        text-transform: uppercase;
    }}
    .harvard-headline {{
        font-size: 10.5pt;
        font-style: italic;
        margin: 0 0 3px 0;
        color: #000000;
    }}
    .harvard-contact {{
        font-size: 9pt;
        color: #000000;
        margin: 0;
    }}
    .harvard-section {{
        margin-top: 8px;
        margin-bottom: 3px;
    }}
    .harvard-section-title {{
        font-size: 10.5pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 1px solid #000000;
        padding-bottom: 1.5px;
        margin: 0 0 5px 0;
        color: #000000;
    }}
    .harvard-summary {{
        margin: 0;
        text-align: justify;
        font-size: 9.5pt;
        line-height: 1.32;
    }}
    .skill-row {{
        margin-bottom: 2px;
        font-size: 9.5pt;
        line-height: 1.3;
    }}
    .skill-cat-label {{
        font-weight: 700;
        color: #000000;
    }}
    .exp-item {{
        margin-bottom: 7px;
        page-break-inside: avoid;
    }}
    .exp-line-top {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }}
    .exp-line-sub {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 2px;
    }}
    .exp-company {{
        font-weight: 700;
        font-size: 9.8pt;
        color: #000000;
    }}
    .exp-title {{
        font-style: italic;
        font-size: 9.5pt;
        color: #000000;
    }}
    .exp-right {{
        font-size: 9pt;
        color: #000000;
        white-space: nowrap;
        text-align: right;
    }}
    .exp-bullets {{
        margin: 2px 0 0 16px;
        padding: 0;
    }}
    .exp-bullets li {{
        margin-bottom: 2.5px;
        text-align: justify;
        font-size: 9.3pt;
        line-height: 1.3;
        color: #000000;
    }}
    .edu-item {{
        margin-bottom: 5px;
        page-break-inside: avoid;
    }}
    .harvard-simple-list {{
        margin: 2px 0 0 16px;
        padding: 0;
        font-size: 9.3pt;
    }}
    .harvard-simple-list li {{
        margin-bottom: 2px;
        color: #000000;
    }}
    .harvard-text {{
        margin: 0;
        font-size: 9.5pt;
        color: #000000;
    }}
</style>
</head>
<body>
    <div class="harvard-header">
        <h1 class="harvard-name">{resume.full_name}</h1>
        <div class="harvard-headline">{resume.target_headline}</div>
        <div class="harvard-contact">{contact_line}</div>
    </div>

    <div class="harvard-section">
        <h2 class="harvard-section-title">Perfil Profesional</h2>
        <p class="harvard-summary">{resume.professional_summary}</p>
    </div>

    <div class="harvard-section">
        <h2 class="harvard-section-title">Competencias Técnicas & Habilidades Clave</h2>
        {categories_html}
    </div>

    <div class="harvard-section">
        <h2 class="harvard-section-title">Experiencia Profesional</h2>
        {exp_html}
    </div>

    <div class="harvard-section">
        <h2 class="harvard-section-title">Educación</h2>
        {edu_html}
    </div>

    {cert_section}

    {lang_section}
</body>
</html>"""

    def generate_tailored_pdf(
        self,
        candidate_data: Dict[str, Any],
        job_info: Dict[str, Any],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        End-to-End: AI Harvard Tailoring -> HTML Harvard Standard -> Playwright PDF export.
        Returns file path, download filename, and preview metadata.
        Strictly guarantees pure monochrome black and <= 2 pages.
        """
        target_dir = output_dir or self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. AI Optimization according to Harvard guidelines
        tailored = self.tailor_cv_with_ai(candidate_data, job_info)

        # 2. HTML Rendering with 100% black Harvard layout
        html_content = self.render_html_template(tailored)

        # 3. Filename formatting with clean ASCII sanitization
        def sanitize_slug(text: str) -> str:
            ascii_text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
            return re.sub(r"[^\w]+", "_", ascii_text).strip("_")

        clean_name = sanitize_slug(tailored.full_name) or "Candidato"
        clean_comp = sanitize_slug(job_info.get("company", "Empresa")) or "Empresa"
        pdf_filename = f"CV_{clean_name}_{clean_comp}.pdf"
        pdf_path = target_dir / pdf_filename

        # 4. Playwright PDF export with strict Letter dimensions
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="Letter",
                print_background=True,
                margin={"top": "12mm", "bottom": "12mm", "left": "15mm", "right": "15mm"}
            )
            browser.close()

        return {
            "status": "success",
            "pdf_filename": pdf_filename,
            "pdf_path": str(pdf_path),
            "tailored_data": tailored.model_dump()
        }
