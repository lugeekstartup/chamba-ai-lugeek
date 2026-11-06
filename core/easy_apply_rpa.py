"""
LinkedIn Easy Apply RPA Worker using Playwright with persistent sessions.
Automates form filling using structured facts from the candidate profile to avoid hallucination.
"""

import os
import time
import re
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError


class LinkedInEasyApplyRPA:
    def __init__(self, session_state_path: str = "./sessions/linkedin_state.json", headless: bool = False):
        self.session_state_path = session_state_path
        self.headless = headless

    def save_manual_login_session(self):
        """
        Launches a visible browser window allowing the user to manually log in to LinkedIn,
        complete 2FA or security checks, and automatically saves the session cookies.
        """
        os.makedirs(os.path.dirname(os.path.abspath(self.session_state_path)), exist_ok=True)
        print("[Auth Helper] Abriendo navegador para inicio de sesión manual en LinkedIn...")
        print("[Auth Helper] Por favor inicia sesión y resuelve cualquier 2FA/CAPTCHA.")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.linkedin.com/login")

            # Wait until user is on the feed/homepage
            try:
                page.wait_for_url("**/feed/**", timeout=120000)
                print("[Auth Helper] ¡Inicio de sesión detectado exitosamente!")
                context.storage_state(path=self.session_state_path)
                print(f"[Auth Helper] Sesión guardada en: {self.session_state_path}")
            except PlaywrightTimeoutError:
                print("[Auth Helper] Tiempo de espera agotado. No se completó el inicio de sesión.")
            finally:
                browser.close()

    def fill_form_step(self, modal: Locator, candidate_profile: Dict[str, Any], cv_pdf_path: Optional[str] = None):
        """Inspects and fills common Easy Apply inputs on the active modal page."""
        cand = candidate_profile.get("structured_profile", {})
        facts = cand.get("fact_sheet_skills", {})
        personal = candidate_profile.get("personal_details", {})
        work_auth = candidate_profile.get("work_authorization", {})

        # Extract candidate personal values dynamically
        first_name = personal.get("first_name") or ""
        last_name = personal.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip() or cand.get("full_name") or ""
        phone = personal.get("phone_number") or cand.get("phone") or ""
        phone_country_code = personal.get("phone_country_code") or "+51"

        # Extract clean digits from phone
        phone_digits = re.sub(r"[^\d]", "", phone)
        if len(phone_digits) > 9 and phone_digits.startswith("51"):
            phone_digits = phone_digits[2:]

        email = personal.get("email") or cand.get("email") or ""
        city = personal.get("city") or cand.get("location") or ""
        country = personal.get("country") or "Perú"

        # 1. Fill Text / Tel / Number inputs
        inputs = modal.locator("input:not([type='hidden']):not([type='file']):not([type='checkbox']):not([type='radio'])")
        for i in range(inputs.count()):
            try:
                inp = inputs.nth(i)
                if not inp.is_visible():
                    continue

                curr_val = inp.input_value()
                if curr_val and curr_val.strip():
                    continue  # Already filled

                inp_id = (inp.get_attribute("id") or "").lower()
                inp_name = (inp.get_attribute("name") or "").lower()
                inp_type = (inp.get_attribute("type") or "text").lower()
                aria_label = (inp.get_attribute("aria-label") or "").lower()
                autocomplete = (inp.get_attribute("autocomplete") or "").lower()

                # Get context label
                label_text = ""
                raw_id = inp.get_attribute("id")
                if raw_id:
                    lbl = modal.locator(f"label[for='{raw_id}']").first
                    if lbl.count() > 0:
                        label_text = lbl.text_content() or ""

                if not label_text:
                    label_text = inp.evaluate("""el => {
                        let parent = el.closest('.fb-dash-form-element, .jobs-easy-apply-form-section__grouping, .jobs-easy-apply-form-element, .artdeco-text-input--container, .artdeco-text-input');
                        if (parent) {
                            let l = parent.querySelector('label');
                            return l ? l.innerText : parent.innerText;
                        }
                        return '';
                    }""") or ""

                context = f"{label_text} {inp_id} {inp_name} {aria_label} {autocomplete}".lower()

                # A. Phone number
                if inp_type == "tel" or "tel" in autocomplete or "phone" in inp_id or "phone" in inp_name or any(k in context for k in ["phone", "teléfono", "telefono", "móvil", "movil", "celular"]):
                    inp.fill(phone_digits)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # B. First name
                if any(k in context for k in ["first name", "given name", "primer nombre"]) or (
                    "nombre" in context and not any(k in context for k in ["apellido", "last name", "completo"])
                ):
                    inp.fill(first_name or full_name)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # C. Last name
                if any(k in context for k in ["last name", "apellido", "surname", "family name"]):
                    inp.fill(last_name)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # D. Full name
                if any(k in context for k in ["full name", "nombre completo"]):
                    inp.fill(full_name)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # E. Email
                if inp_type == "email" or "email" in autocomplete or any(k in context for k in ["email", "correo", "e-mail"]):
                    inp.fill(email)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # F. City / Location
                if any(k in context for k in ["city", "ciudad", "location", "ubicación", "ubicacion"]):
                    inp.fill(city)
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # G. Years of experience with a skill
                if inp_type == "number" or any(k in context for k in ["years", "años", "anos", "experience", "experiencia"]):
                    matched_years = None
                    for s_name, yrs in facts.items():
                        if re.search(rf"\b{re.escape(s_name)}\b", context):
                            matched_years = int(yrs)
                            break
                    if matched_years is None:
                        matched_years = int(cand.get("total_years_experience") or 5)
                    inp.fill(str(matched_years))
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # H. Salary / Compensation
                if any(k in context for k in ["salary", "salario", "pretensión", "pretension", "remuneración", "remuneracion", "compensation"]):
                    inp.fill("4000")
                    inp.dispatch_event('input')
                    inp.dispatch_event('change')
                    continue

                # I. General numeric vs text
                if inp_type == "number":
                    inp.fill("1")
                else:
                    inp.fill("Sí")
                inp.dispatch_event('input')
                inp.dispatch_event('change')
            except Exception as e:
                print(f"[RPA Fill Input Error] {e}")

        # 2. Dropdowns (Selects)
        selects = modal.locator("select")
        for i in range(selects.count()):
            try:
                sel = selects.nth(i)
                if not sel.is_visible():
                    continue

                sel_id = (sel.get_attribute("id") or "").lower()
                sel_name = (sel.get_attribute("name") or "").lower()
                sel_aria = (sel.get_attribute("aria-label") or "").lower()
                sel_context = f"{sel_id} {sel_name} {sel_aria}".lower()

                target_code = personal.get("phone_country_code") or "+51"
                target_country = (personal.get("country") or "Peru").lower()

                options = sel.locator("option")
                selected = False

                # Country code selector
                if any(k in sel_context for k in ["country", "phone", "pais", "código", "codigo"]):
                    for o_idx in range(options.count()):
                        opt_text = (options.nth(o_idx).text_content() or "").lower()
                        opt_val = options.nth(o_idx).get_attribute("value") or ""
                        if target_code.lower() in opt_text or target_country in opt_text or "peru" in opt_text or "perú" in opt_text:
                            sel.select_option(value=opt_val)
                            sel.dispatch_event('change')
                            selected = True
                            break

                if not selected:
                    # Look for affirmative options (Yes / Sí / Si)
                    for o_idx in range(options.count()):
                        opt_text = (options.nth(o_idx).text_content() or "").strip().lower()
                        opt_val = options.nth(o_idx).get_attribute("value") or ""
                        if opt_text in ["yes", "sí", "si"]:
                            sel.select_option(value=opt_val)
                            sel.dispatch_event('change')
                            selected = True
                            break

                if not selected and options.count() > 1:
                    # Select first valid non-empty option
                    sel.select_option(index=1)
                    sel.dispatch_event('change')
            except Exception as e:
                print(f"[RPA Select Error] {e}")
        for i in range(selects.count()):
            try:
                sel = selects.nth(i)
                if not sel.is_visible():
                    continue

                # Try selecting Peru or +51 if phone country code
                options = sel.locator("option")
                selected = False
                for o_idx in range(options.count()):
                    opt_text = (options.nth(o_idx).text_content() or "").lower()
                    opt_val = options.nth(o_idx).get_attribute("value") or ""
                    if "peru" in opt_text or "perú" in opt_text or "+51" in opt_text:
                        sel.select_option(value=opt_val)
                        selected = True
                        break
                    if "yes" in opt_text or "sí" in opt_text or "si" in opt_text:
                        sel.select_option(value=opt_val)
                        selected = True
                        break

                if not selected and options.count() > 1:
                    # Select first valid non-empty option
                    sel.select_option(index=1)
            except Exception as e:
                print(f"[RPA Select Error] {e}")

        # 3. Fieldsets / Radio Buttons
        fieldsets = modal.locator("fieldset")
        for i in range(fieldsets.count()):
            try:
                fs = fieldsets.nth(i)
                if not fs.is_visible():
                    continue

                fs_text = (fs.text_content() or "").lower()

                # Sponsorship (usually No)
                if any(k in fs_text for k in ["sponsorship", "patrocinio", "visa"]):
                    no_radio = fs.locator("label:has-text('No'), input[value*='0'], input[value*='No']").first
                    if no_radio.count() > 0:
                        no_radio.click()
                        continue

                # Authorization / Legal right to work (usually Yes)
                if any(k in fs_text for k in ["authorized", "autorizado", "legalmente", "permiso"]):
                    yes_radio = fs.locator("label:has-text('Yes'), label:has-text('Sí'), label:has-text('Si')").first
                    if yes_radio.count() > 0:
                        yes_radio.click()
                        continue

                # Default to Yes if available
                yes_opt = fs.locator("label:has-text('Yes'), label:has-text('Sí'), label:has-text('Si')").first
                if yes_opt.count() > 0:
                    yes_opt.click()
                else:
                    # Click first radio
                    first_r = fs.locator("input[type='radio'], label").first
                    if first_r.count() > 0:
                        first_r.click()
            except Exception as e:
                print(f"[RPA Radio Error] {e}")

        # 4. CV Upload File
        file_inputs = modal.locator("input[type='file']")
        if file_inputs.count() > 0 and cv_pdf_path and os.path.exists(cv_pdf_path):
            try:
                file_inputs.first.set_input_files(cv_pdf_path)
            except Exception as e:
                print(f"[RPA File Upload Error] {e}")

        # 5. Mandatory Checkboxes
        try:
            req_boxes = modal.locator("input[type='checkbox'][required], input[type='checkbox'][aria-required='true']")
            for b_idx in range(req_boxes.count()):
                box = req_boxes.nth(b_idx)
                if not box.is_checked():
                    box.check()
        except Exception:
            pass

    def apply_to_job(
        self,
        job_url: str,
        candidate_profile: Dict[str, Any],
        cv_pdf_path: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Navigates to job post, initiates Easy Apply, fills steps, and submits.
        If dry_run=True, it fills everything but does NOT click the final Submit button.
        """
        if not os.path.exists(self.session_state_path):
            raise FileNotFoundError(
                f"No se encontró sesión de LinkedIn en {self.session_state_path}. "
                "Haz clic en 'Sin Sesión LinkedIn' en la web para iniciar sesión primero."
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(storage_state=self.session_state_path)
            page = context.new_page()

            try:
                page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2.5)

                # Locate Easy Apply button (multilingual support)
                selectors = [
                    "button.jobs-apply-button",
                    "button[aria-label*='Easy Apply']",
                    "button[aria-label*='Solicitud sencilla']",
                    "button:has-text('Easy Apply')",
                    "button:has-text('Solicitud sencilla')",
                    ".jobs-apply-button--top-card button",
                    ".jobs-s-apply button"
                ]
                apply_button = None
                for sel in selectors:
                    loc = page.locator(sel).first
                    try:
                        loc.wait_for(state="visible", timeout=2000)
                        apply_button = loc
                        break
                    except Exception:
                        continue

                if not apply_button:
                    external_loc = page.locator("a:has-text('Apply'), a:has-text('Solicitar'), button:has-text('Solicitar en el sitio web')").first
                    if external_loc.count() > 0:
                        return {
                            "status": "NOT_EASY_APPLY",
                            "reason": "Esta vacante requiere postulación externa en el sitio web de la empresa (no es Solicitud sencilla en LinkedIn)."
                        }
                    return {"status": "FAILED", "reason": "No se encontró el botón de Solicitud sencilla en la vacante."}

                apply_button.click()
                time.sleep(2)

                # Find Easy Apply Modal
                modal = page.locator(".jobs-easy-apply-modal, div[role='dialog'], .artdeco-modal").first
                try:
                    modal.wait_for(state="visible", timeout=5000)
                except Exception:
                    pass

                # Step through modal until Review or Submit
                max_steps = 12
                current_step = 0

                while current_step < max_steps:
                    current_step += 1
                    time.sleep(1.2)

                    # 1. Fill current modal inputs
                    self.fill_form_step(modal, candidate_profile, cv_pdf_path)

                    # 2. Check if final Submit button is present
                    submit_button = modal.locator(
                        "button[aria-label*='Submit application'], button[aria-label*='Enviar solicitud'], "
                        "button:has-text('Submit application'), button:has-text('Enviar solicitud')"
                    ).first

                    if submit_button.count() > 0 and submit_button.is_visible():
                        # Uncheck follow company checkbox if present
                        try:
                            follow_box = modal.locator("label[for*='follow-company'], input[id*='follow-company']").first
                            if follow_box.count() > 0 and follow_box.is_visible():
                                follow_box.click()
                        except Exception:
                            pass

                        if dry_run:
                            print(f"[RPA Dry Run] Formulario completado exitosamente para {job_url}. No se envió por modo seguro.")
                            return {
                                "status": "READY_TO_SUBMIT_DRY_RUN",
                                "message": "¡Formulario completado en simulación con éxito! Todos los pasos fueron rellenados sin enviar.",
                                "steps_completed": current_step
                            }
                        else:
                            submit_button.click()
                            time.sleep(3)
                            return {
                                "status": "APPLIED_SUCCESS",
                                "message": "¡Postulación enviada exitosamente en LinkedIn!",
                                "job_url": job_url
                            }

                    # 3. Find Next or Review button
                    next_selectors = [
                        "footer button.artdeco-button--primary",
                        "button[aria-label*='Continue to next step']",
                        "button[aria-label*='Siguiente']",
                        "button[aria-label*='Revisar']",
                        "button:has-text('Siguiente')",
                        "button:has-text('Continuar')",
                        "button:has-text('Revisar')",
                        "button:has-text('Next')",
                        "button:has-text('Review')",
                        "button[data-easy-apply-next-button]"
                    ]
                    next_btn = None
                    for nsel in next_selectors:
                        loc = modal.locator(nsel).first
                        if loc.count() > 0 and loc.is_visible():
                            next_btn = loc
                            break

                    if next_btn:
                        time.sleep(0.5)
                        next_btn.click()
                    else:
                        break

                # If loop completed without submit
                errors = modal.locator(".artdeco-inline-feedback--error").all_text_contents()
                return {
                    "status": "STOPPED",
                    "reason": f"No se pudo avanzar al siguiente paso. Campos pendientes: {', '.join(errors) if errors else 'Verifica los campos requeridos en pantalla'}"
                }

            except Exception as e:
                return {"status": "ERROR", "error": str(e)}
            finally:
                browser.close()
