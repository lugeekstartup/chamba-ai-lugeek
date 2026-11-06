"""
LinkedIn Guest API Scraper using curl_cffi for resilient, anti-bot-safe job discovery.
Extracts jobs without needing authentication or launching heavy browsers.
"""

import time
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from curl_cffi import requests
from bs4 import BeautifulSoup


class LinkedInScraper:
    BASE_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOB_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting"

    def __init__(self, proxy: Optional[str] = None):
        self.session = requests.Session(impersonate="chrome124")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        })

    @staticmethod
    def is_job_posting_closed(status_code: int, html_text: str) -> bool:
        """Determines if a LinkedIn job posting is inactive, closed, expired, or deleted."""
        if status_code in (404, 410, 403):
            return True
        if not html_text:
            return True
        lower = html_text.lower()
        closed_signals = [
            "no longer accepting applications",
            "ya no se aceptan solicitudes",
            "ya no acepta solicitudes",
            "no se aceptan más solicitudes",
            "closed-job",
            "job-expired",
            "job is closed",
            "job posting is closed",
            "esta oferta de empleo ya no está disponible",
            "la oferta de empleo ha expirado",
            "oferta de empleo caducada",
            "oferta cerrada",
            "has expired",
            "este empleo ya no se encuentra disponible",
            "no se encontró la página",
            "the job you are trying to view is no longer available",
            "this job is no longer available",
            "closed-job__flavor",
            "closed-job__header",
            "data-job-status=\"closed\""
        ]
        return any(sig in lower for sig in closed_signals)

    @staticmethod
    def detect_destination_portal(html_text: str, company: str, is_easy: bool) -> str:
        """Identifies the true application destination ATS or portal (Workday, Lever, Greenhouse, etc.)."""
        if is_easy:
            return "LinkedIn (Easy Apply)"
        lower = html_text.lower() if html_text else ""
        ats_patterns = [
            ("myworkdayjobs.com", "Workday"),
            ("workday", "Workday"),
            ("greenhouse.io", "Greenhouse"),
            ("greenhouse", "Greenhouse"),
            ("jobs.lever.co", "Lever"),
            ("lever.co", "Lever"),
            ("smartrecruiters.com", "SmartRecruiters"),
            ("smartrecruiters", "SmartRecruiters"),
            ("taleo.net", "Oracle Taleo"),
            ("oraclecloud", "Oracle Cloud HCM"),
            ("taleo", "Oracle Taleo"),
            ("bamboohr.com", "BambooHR"),
            ("ashbyhq.com", "Ashby"),
            ("workable.com", "Workable"),
            ("computrabajo", "Computrabajo"),
            ("bumeran", "Bumeran"),
            ("talana", "Talana"),
            ("jobs.personio", "Personio"),
            ("breezy.hr", "Breezy HR"),
            ("evaluar.com", "Evaluar.com"),
            ("pandape", "PandaPe"),
            ("manpower", "Manpower"),
            ("adecco", "Adecco"),
        ]
        for pattern, name in ats_patterns:
            if pattern in lower:
                return name
        clean_comp = (company or "").strip()
        if clean_comp and clean_comp.lower() not in ("unknown", "confidencial"):
            return f"Sitio Web de {clean_comp}"
        return "Sitio Web de la Empresa"

    def search_jobs(
        self,
        keywords: str,
        location: str = "Lima, Perú",
        remote: bool = True,
        modalities: Optional[List[str]] = None,
        date_range: Optional[str] = None,
        easy_apply_only: bool = True,
        max_results: int = 25,
        delay_seconds: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Searches LinkedIn job postings using the public guest endpoint.
        Filters out expired/closed job postings.
        """
        results = []
        start = 0

        loc_clean = (location or "").strip()
        if not loc_clean or loc_clean.lower() == "worldwide":
            loc_clean = "Lima, Perú"

        # Build query parameters
        params = [
            f"keywords={quote(keywords)}",
            f"location={quote(loc_clean)}",
            "sortBy=DD"  # Sort by most recent
        ]

        # 1. Modality mapping (Remote, Hybrid, On-site)
        wt_codes = []
        if modalities:
            mod_map = {
                "REMOTE": "2",
                "HYBRID": "3",
                "ON_SITE": "1"
            }
            for m in modalities:
                code = mod_map.get(m.upper())
                if code and code not in wt_codes:
                    wt_codes.append(code)
        elif remote:
            wt_codes.append("2")

        if wt_codes:
            params.append(f"f_WT={'%2C'.join(wt_codes)}")

        # 2. Date Range mapping (24h, semana, mes)
        date_map = {
            "past_24h": "r86400",
            "past_week": "r604800",
            "past_month": "r2592000"
        }
        if date_range and date_range in date_map:
            params.append(f"f_TPR={date_map[date_range]}")

        # 3. Easy Apply
        if easy_apply_only:
            params.append("f_LF=f_AL")

        while len(results) < max_results:
            url = f"{self.BASE_SEARCH_URL}?{'&'.join(params)}&start={start}"
            
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all("li")
                if not cards:
                    break

                for card in cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")
                    time_elem = card.find("time")

                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    raw_link = link_elem.get("href", "").split("?")[0]
                    date_posted = time_elem.get("datetime") if time_elem else ""

                    # Extract clean 8+ digit LinkedIn Job ID from the link
                    job_id_match = re.search(r"-(\d{8,})(?:\?|$)", raw_link) or re.search(r"(\d{8,})", raw_link)
                    job_id = job_id_match.group(1) if job_id_match else ""

                    if not job_id:
                        continue

                    # Verify if job is active and check for Easy Apply
                    is_active = True
                    is_easy = False
                    dest_portal = f"Sitio Web de {company}" if company and company.lower() != "unknown" else "Sitio de la Empresa"

                    try:
                        check_resp = self.session.get(f"{self.JOB_DETAIL_URL}/{job_id}", timeout=8)
                        if self.is_job_posting_closed(check_resp.status_code, check_resp.text):
                            is_active = False
                        else:
                            is_easy = ("apply-link-onsite" in check_resp.text) and ("apply-link-offsite" not in check_resp.text)
                            dest_portal = self.detect_destination_portal(check_resp.text, company, is_easy)
                    except Exception:
                        pass

                    if not is_active:
                        # Skip closed or non-existent jobs
                        continue

                    # If filtering strictly for Easy Apply, skip external apply jobs
                    if easy_apply_only and not is_easy:
                        continue

                    results.append({
                        "job_id": job_id,
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                        "date_posted": date_posted,
                        "portal": "LINKEDIN",
                        "destination_portal": dest_portal,
                        "is_easy_apply": is_easy
                    })

                    if len(results) >= max_results:
                        break

                start += 25
                time.sleep(delay_seconds)

            except Exception as e:
                print(f"[Scraper Error] Failed fetching batch start={start}: {e}")
                break

        return results

    def fetch_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the full description and criteria for a specific job."""
        url = f"{self.JOB_DETAIL_URL}/{job_id}"
        try:
            resp = self.session.get(url, timeout=15)
            if self.is_job_posting_closed(resp.status_code, resp.text):
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            desc_elem = soup.find("div", class_="show-more-less-html__markup")
            raw_description = desc_elem.get_text("\n", strip=True) if desc_elem else ""

            criteria = {}
            criteria_items = soup.find_all("li", class_="description__job-criteria-item")
            for item in criteria_items:
                header = item.find("h3")
                val = item.find("span")
                if header and val:
                    criteria[header.get_text(strip=True).lower()] = val.get_text(strip=True)

            is_easy = ("apply-link-onsite" in resp.text) and ("apply-link-offsite" not in resp.text)
            company_name = criteria.get("company", "")
            dest_portal = self.detect_destination_portal(resp.text, company_name, is_easy)

            return {
                "job_id": job_id,
                "description": raw_description,
                "employment_type": criteria.get("employment type", "Full-time"),
                "seniority_level": criteria.get("seniority level", "Not Specified"),
                "job_function": criteria.get("job function", ""),
                "destination_portal": dest_portal,
                "is_easy_apply": is_easy
            }
        except Exception as e:
            print(f"[Detail Error] Failed to get details for job {job_id}: {e}")
            return None
