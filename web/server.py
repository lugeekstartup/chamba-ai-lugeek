"""
Chamba AI - Community Edition: Web Server
Standalone, single-user FastAPI application for LinkedIn job searching,
semantic matching, and Harvard ATS resume tailoring.
Zero authentication barriers, local JSON storage, and UI-configurable OpenAI credentials.
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

# Core Engine Modules
from core.linkedin_scraper import LinkedInScraper
from core.cv_parser import CVParser
from core.matching_engine import MatchingEngine
from core.cv_tailor import CVTailor

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
TAILORED_DIR = DATA_DIR / "tailored_resumes"
CONFIG_FILE = CONFIG_DIR / "settings.json"
PROFILE_FILE = DATA_DIR / "parsed_candidate_profile.json"
JOBS_FILE = DATA_DIR / "scraped_jobs.json"
MATCHES_FILE = DATA_DIR / "evaluated_matches.json"

for d in [CONFIG_DIR, DATA_DIR, TAILORED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Chamba AI Lugeek",
    description="Búsqueda de trabajo eficaz con la IA — Edición Comunitaria",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# CONFIGURATION HELPERS
# -------------------------------------------------------------

def load_settings() -> Dict[str, Any]:
    default_settings = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL", ""),
        "candidate_preferences": {
            "keywords": ["Software Engineer", "Full Stack", "Data", "Tech Lead"],
            "location": "Lima, Perú",
            "modalities": ["REMOTE", "HYBRID"],
            "easy_apply_only": True
        }
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_settings.update(loaded)
                return default_settings
        except Exception:
            pass
    return default_settings


def save_settings(data: Dict[str, Any]):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_active_openai_credentials(override_key: Optional[str] = None, override_model: Optional[str] = None, override_base_url: Optional[str] = None):
    settings = load_settings()
    api_key = override_key or settings.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    model = override_model or settings.get("openai_model") or os.getenv("OPENAI_MODEL", "gpt-6-luna")
    base_url = override_base_url or settings.get("openai_base_url") or os.getenv("OPENAI_BASE_URL")
    if base_url and not str(base_url).strip():
        base_url = None
    elif base_url:
        base_url = str(base_url).strip()
    return api_key, model, base_url


def mask_key(k: str) -> str:
    if not k:
        return ""
    if len(k) <= 8:
        return "****"
    return f"{k[:4]}...{k[-4:]}"


# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------

class AIConfigRequest(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = "gpt-6-luna"
    openai_base_url: Optional[str] = None
    candidate_preferences: Optional[Dict[str, Any]] = None


class PersonalDetailsRequest(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    email: Optional[str] = ""
    phone_country_code: Optional[str] = "+51"
    phone_number: Optional[str] = ""
    city: Optional[str] = "Lima"
    country: Optional[str] = "Perú"


class JobSearchRequest(BaseModel):
    keywords: str = "Software Engineer"
    location: str = "Lima, Perú"
    remote: bool = True
    modalities: Optional[List[str]] = Field(default=["REMOTE", "HYBRID"])
    date_range: Optional[str] = "past_month"
    easy_apply_only: bool = True
    limit: int = 25


class TailoredCVRequest(BaseModel):
    job_id: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


# -------------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/health")
def api_health():
    return {
        "status": "ok",
        "app": "Chamba AI Lugeek",
        "description": "Búsqueda de trabajo eficaz con la IA",
        "version": "1.0.0"
    }


@app.get("/api/config")
def api_get_config():
    settings = load_settings()
    raw_key = settings.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
    return {
        "has_openai_key": bool(raw_key),
        "masked_api_key": mask_key(raw_key),
        "openai_model": settings.get("openai_model") or os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        "openai_base_url": settings.get("openai_base_url") or os.getenv("OPENAI_BASE_URL", ""),
        "candidate_preferences": settings.get("candidate_preferences", {})
    }


@app.post("/api/config")
def api_save_config(req: AIConfigRequest):
    settings = load_settings()
    if req.openai_api_key is not None:
        settings["openai_api_key"] = req.openai_api_key.strip()
    if req.openai_model:
        settings["openai_model"] = req.openai_model.strip()
    if req.openai_base_url is not None:
        settings["openai_base_url"] = req.openai_base_url.strip()
    if req.candidate_preferences is not None:
        settings["candidate_preferences"] = req.candidate_preferences

    save_settings(settings)
    raw_key = settings.get("openai_api_key", "")
    return {
        "status": "success",
        "message": "Configuración guardada correctamente.",
        "has_openai_key": bool(raw_key),
        "masked_api_key": mask_key(raw_key),
        "openai_model": settings.get("openai_model"),
        "openai_base_url": settings.get("openai_base_url", "")
    }


@app.post("/api/test-openai-connection")
def api_test_openai_connection(req: AIConfigRequest):
    api_key = (req.openai_api_key or "").strip()
    model = (req.openai_model or "").strip()
    base_url = (req.openai_base_url or "").strip() if req.openai_base_url is not None else None

    # Fall back to saved credentials if not specified in request
    saved_key, saved_model, saved_base_url = get_active_openai_credentials()
    if not api_key:
        api_key = saved_key
    if not model:
        model = saved_model or "gpt-6-luna"
    if base_url is None:
        base_url = saved_base_url

    if not api_key:
        raise HTTPException(status_code=400, detail="Por favor ingresa una API Key para probar la conexión.")

    clean_base_url = base_url.strip() if base_url and base_url.strip() else None

    try:
        client = OpenAI(api_key=api_key, base_url=clean_base_url)
        # Test lightweight completion
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hola"}],
            max_tokens=10
        )
        endpoint_info = clean_base_url if clean_base_url else "OpenAI Oficial"
        return {
            "status": "success",
            "message": f"Conexión exitosa con el modelo '{model}' en el endpoint '{endpoint_info}'. Respuesta recibida correctamente."
        }
    except Exception as e:
        endpoint_msg = f" (Endpoint: {clean_base_url})" if clean_base_url else ""
        raise HTTPException(status_code=400, detail=f"Error conectando con la API{endpoint_msg}: {str(e)}")


@app.get("/api/current-profile")
def api_get_current_profile():
    """Returns the parsed profile and active candidate facts."""
    if not PROFILE_FILE.exists():
        return None
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sp = data.get("structured_profile", {})
        if not sp:
            sp = dict(data)
        
        if not sp.get("skills_inventory"):
            sp["skills_inventory"] = sp.get("skills_with_years", [])
        if not sp.get("skills_with_years"):
            sp["skills_with_years"] = sp.get("skills_inventory", [])
        if not sp.get("professional_summary"):
            sp["professional_summary"] = sp.get("headline_or_role", "")
        if not sp.get("education"):
            sp["education"] = data.get("education", [])
        if not sp.get("certifications"):
            sp["certifications"] = data.get("certifications", [])
        if not sp.get("languages"):
            sp["languages"] = data.get("languages", [])

        data["structured_profile"] = sp
        return data
    except Exception as e:
        print(f"[Profile Warning] Could not read profile file: {e}")
        return None


@app.post("/api/candidate-details")
def api_save_candidate_details(req: PersonalDetailsRequest):
    """Updates candidate personal facts (name, email, phone, city, country)."""
    current_data = {}
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass

    current_data["personal_details"] = req.model_dump()
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "message": "Datos personales actualizados correctamente.",
        "personal_details": req.model_dump()
    }


@app.post("/api/upload-cv")
async def api_upload_cv(file: UploadFile = File(...)):
    """Receives a PDF CV, parses it with OpenAI Structured Outputs, and generates the Fact Sheet."""
    api_key, model, base_url = get_active_openai_credentials()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Se requiere una API Key para procesar el CV con IA. Ingrésala en la pestaña de Configuración."
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo PDF excede el límite máximo de 10 MB.")

    save_path = DATA_DIR / "uploaded_cv.pdf"
    with open(save_path, "wb") as buffer:
        buffer.write(file_bytes)

    try:
        parser = CVParser(api_key=api_key, model=model, base_url=base_url)
        parsed = parser.process_cv_file(str(save_path), output_json_path=str(PROFILE_FILE))
        cand_prof = parsed.get("structured_profile", {})

        # Extract personal details dynamically
        full_name = (cand_prof.get("full_name") or "").strip()
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        raw_phone = cand_prof.get("phone") or ""
        country_code = "+51"
        phone_num = raw_phone
        if raw_phone.startswith("+"):
            m = re.match(r"^(\+\d{1,3})\s*(.*)$", raw_phone)
            if m:
                country_code = m.group(1)
                phone_num = m.group(2)
        phone_digits = re.sub(r"[^\d]", "", phone_num)

        loc = cand_prof.get("location") or ""
        city = ""
        country = ""
        if "," in loc:
            parts = [p.strip() for p in loc.split(",")]
            city = parts[0]
            country = parts[-1]
        else:
            city = loc.strip()
            country = "Perú" if "peru" in loc.lower() or "perú" in loc.lower() else ""

        personal_details = {
            "first_name": first_name,
            "last_name": last_name,
            "email": cand_prof.get("email") or "",
            "phone_country_code": country_code,
            "phone_number": phone_digits or raw_phone,
            "city": city or "Lima",
            "country": country or "Perú"
        }

        # Save personal details into profile file
        parsed["personal_details"] = personal_details
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        cand_prof["skills_inventory"] = cand_prof.get("skills_with_years", [])
        cand_prof["professional_summary"] = cand_prof.get("headline_or_role", "")

        return {
            "status": "success",
            "profile": cand_prof,
            "personal_details": personal_details,
            "cv_filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando CV con IA: {str(e)}")


@app.post("/api/search-jobs")
def api_search_jobs(req: JobSearchRequest):
    """Searches LinkedIn for jobs using public guest scraping."""
    scraper = LinkedInScraper()
    jobs = scraper.search_jobs(
        keywords=req.keywords,
        location=req.location,
        remote=req.remote,
        modalities=req.modalities,
        date_range=req.date_range,
        easy_apply_only=req.easy_apply_only,
        max_results=req.limit
    )

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "count": len(jobs),
        "jobs": jobs
    }


@app.get("/api/saved-jobs")
def api_get_saved_jobs():
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


@app.post("/api/evaluate-matches")
def api_evaluate_matches():
    """Scores discovered LinkedIn jobs against the candidate profile using OpenAI or custom Luna provider."""
    api_key, model, base_url = get_active_openai_credentials()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Se requiere una API Key para evaluar los puestos con IA. Ingrésala en Configuración."
        )

    if not PROFILE_FILE.exists():
        raise HTTPException(status_code=400, detail="Debes cargar un CV en PDF primero (Paso 1).")
    if not JOBS_FILE.exists():
        raise HTTPException(status_code=400, detail="Debes buscar empleos en LinkedIn primero (Paso 2).")

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        profile_data = json.load(f)
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not jobs:
        raise HTTPException(status_code=400, detail="No hay empleos para evaluar. Realiza una búsqueda primero.")

    scraper = LinkedInScraper()
    engine = MatchingEngine(api_key=api_key, model=model, base_url=base_url)
    settings = load_settings()
    cand_conditions = settings.get("candidate_preferences", {})

    evaluated = []
    # Evaluate top 10 jobs to balance speed and quality
    for job in jobs[:10]:
        if not engine.evaluate_hard_filters(job, cand_conditions):
            continue

        detail = scraper.fetch_job_details(job["job_id"])
        if detail and detail.get("description"):
            job["description"] = detail["description"]
        else:
            job["description"] = f"Puesto: {job['title']} en {job['company']}."

        cand_dict = profile_data.get("structured_profile", {})
        try:
            decision = engine.evaluate_job_fit_with_ai(cand_dict, job)
            job_copy = dict(job)
            job_copy["evaluation"] = decision.model_dump()
            evaluated.append(job_copy)
        except Exception as e:
            print(f"[Matching Warning] Error evaluating job {job.get('job_id')}: {e}")

    evaluated.sort(key=lambda x: x.get("evaluation", {}).get("match_score", 0), reverse=True)

    with open(MATCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(evaluated, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "evaluated_count": len(evaluated),
        "matches": evaluated
    }


@app.get("/api/saved-matches")
def api_get_saved_matches():
    if MATCHES_FILE.exists():
        try:
            with open(MATCHES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


@app.post("/api/generate-tailored-cv")
def api_generate_tailored_cv(req: TailoredCVRequest):
    """Adapts candidate CV to the specific job using AI and exports Harvard ATS PDF."""
    api_key, model, base_url = get_active_openai_credentials()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Se requiere una API Key para generar el CV ATS con IA. Ingrésala en Configuración."
        )

    if not PROFILE_FILE.exists():
        raise HTTPException(status_code=400, detail="Debes cargar un CV en PDF primero (Paso 1).")

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    cand_dict = profile_data.get("structured_profile") or profile_data
    if not isinstance(cand_dict, dict):
        cand_dict = dict(profile_data)

    # Ensure education, certs, and languages
    if "education" not in cand_dict or not cand_dict["education"]:
        cand_dict["education"] = profile_data.get("education", [])
    if "certifications" not in cand_dict or not cand_dict["certifications"]:
        cand_dict["certifications"] = profile_data.get("certifications", [])
    if "languages" not in cand_dict or not cand_dict["languages"]:
        cand_dict["languages"] = profile_data.get("languages", [])

    # Personal facts override
    personal = profile_data.get("personal_details", {})
    if personal:
        full_name = f"{personal.get('first_name', '')} {personal.get('last_name', '')}".strip()
        if full_name:
            cand_dict["full_name"] = full_name
        if personal.get("email"):
            cand_dict["email"] = personal["email"]
        if personal.get("phone_number"):
            cc = personal.get("phone_country_code", "")
            cand_dict["phone"] = f"{cc} {personal['phone_number']}".strip()
        if personal.get("city") or personal.get("country"):
            cand_dict["location"] = f"{personal.get('city', '')}, {personal.get('country', '')}".strip(", ")

    # Fetch description if short
    description = req.description or ""
    company = req.company or "Empresa"
    title = req.title or "Puesto TI"
    location = req.location or "Remoto"

    if len(description) < 50:
        try:
            scraper = LinkedInScraper()
            detail = scraper.fetch_job_details(req.job_id)
            if detail and detail.get("description"):
                description = detail.get("description", "")
                company = detail.get("company", company)
                title = detail.get("title", title)
        except Exception as e:
            print(f"[Tailor Warning] Error fetching job details for {req.job_id}: {e}")

    job_info = {
        "job_id": req.job_id,
        "title": title,
        "company": company,
        "location": location,
        "description": description or f"Puesto: {title} en {company}."
    }

    try:
        tailor = CVTailor(api_key=api_key, model=model, base_url=base_url, output_dir=TAILORED_DIR)
        res = tailor.generate_tailored_pdf(cand_dict, job_info)

        return {
            "status": "success",
            "filename": res["pdf_filename"],
            "download_url": f"/api/download-cv/{res['pdf_filename']}",
            "tailored_data": res["tailored_data"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando CV adaptado ATS: {str(e)}")


@app.get("/api/download-cv/{filename}")
def api_download_cv(filename: str):
    """Downloads the generated Harvard ATS PDF resume."""
    pdf_path = TAILORED_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="El archivo PDF solicitado no fue encontrado.")

    return FileResponse(
        path=str(pdf_path),
        filename=filename,
        media_type="application/pdf"
    )


@app.post("/api/clear-all-data")
def api_clear_all_data():
    """Cleans all search results, matches, and uploaded CV files for a fresh session."""
    try:
        for f in [PROFILE_FILE, JOBS_FILE, MATCHES_FILE, DATA_DIR / "uploaded_cv.pdf"]:
            if f.exists():
                f.unlink()
        
        # Clean tailored resumes folder
        if TAILORED_DIR.exists():
            shutil.rmtree(TAILORED_DIR)
            TAILORED_DIR.mkdir(parents=True, exist_ok=True)

        return {"status": "success", "message": "Todos los registros e historial han sido eliminados correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al limpiar datos: {str(e)}")


# -------------------------------------------------------------
# STATIC FILES SERVING (WEB UI)
# -------------------------------------------------------------

STATIC_DIR = BASE_DIR / "web" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(STATIC_DIR / "index.html"))
