/**
 * Chamba AI — Community Edition Frontend Controller
 * Autonomous LinkedIn Scraping, CV Fact Sheet Extraction & Harvard ATS Resume Generator.
 */

let currentProfile = null;
let savedJobs = [];
let savedMatches = [];
let hasOpenAiKey = false;

// -------------------------------------------------------------
// INITIALIZATION & TAB NAVIGATION
// -------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setupDropZone();
  initApp();
});

async function initApp() {
  await Promise.allSettled([
    loadConfig(),
    loadCurrentProfile(),
    loadSavedJobs(),
    loadSavedMatches()
  ]);
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('border-brand-600', 'text-brand-600', 'dark:text-brand-400');
    btn.classList.add('border-transparent', 'text-slate-500');
  });

  const activePane = document.getElementById(`tab-${tabId}`);
  if (activePane) activePane.classList.remove('hidden');

  const activeBtn = document.getElementById(`tabBtn-${tabId}`);
  if (activeBtn) {
    activeBtn.classList.add('border-brand-600', 'text-brand-600', 'dark:text-brand-400');
    activeBtn.classList.remove('border-transparent', 'text-slate-500');
  }
}

// -------------------------------------------------------------
// THEME (DARK / LIGHT MODE)
// -------------------------------------------------------------

function initTheme() {
  const saved = localStorage.getItem('chamba_theme');
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

function toggleDarkMode() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('chamba_theme', isDark ? 'dark' : 'light');
}

// -------------------------------------------------------------
// AI CONFIGURATION MODAL & CREDENTIALS
// -------------------------------------------------------------

function checkCustomModelVisibility() {
  const select = document.getElementById('selectModel');
  const wrapper = document.getElementById('customModelWrapper');
  if (!select || !wrapper) return;
  if (select.value === 'custom') {
    wrapper.classList.remove('hidden');
    const inputCustom = document.getElementById('inputCustomModel');
    if (inputCustom && !inputCustom.value) {
      inputCustom.focus();
    }
  } else {
    wrapper.classList.add('hidden');
  }
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) return;
    const data = await res.json();
    hasOpenAiKey = data.has_openai_key;

    const dot = document.getElementById('aiStatusDot');
    const text = document.getElementById('aiStatusText');
    const banner = document.getElementById('aiNoticeBanner');

    if (hasOpenAiKey) {
      if (dot) {
        dot.className = 'w-2 h-2 rounded-full bg-emerald-500';
      }
      if (text) {
        text.textContent = 'IA Conectada';
      }
      if (banner) {
        banner.classList.add('hidden');
      }
    } else {
      if (dot) {
        dot.className = 'w-2 h-2 rounded-full bg-amber-500';
      }
      if (text) {
        text.textContent = 'Configurar IA';
      }
      if (banner) {
        banner.classList.remove('hidden');
      }
    }

    if (data.openai_base_url && document.getElementById('inputBaseUrl')) {
      document.getElementById('inputBaseUrl').value = data.openai_base_url;
    }

    if (data.openai_model && document.getElementById('selectModel')) {
      const select = document.getElementById('selectModel');
      const optExists = Array.from(select.options).some(o => o.value === data.openai_model);
      if (optExists) {
        select.value = data.openai_model;
        checkCustomModelVisibility();
      } else {
        select.value = 'custom';
        checkCustomModelVisibility();
        const inputCustom = document.getElementById('inputCustomModel');
        if (inputCustom) inputCustom.value = data.openai_model;
      }
    }
    
    if (document.getElementById('apiKeyStatus')) {
      let statusStr = '';
      if (data.masked_api_key) {
        statusStr += `Clave activa: ${data.masked_api_key}`;
      }
      if (data.openai_base_url) {
        statusStr += ` | Endpoint: ${data.openai_base_url}`;
      }
      document.getElementById('apiKeyStatus').textContent = statusStr;
    }
  } catch (err) {
    console.error('Error cargando configuración:', err);
  }
}

function openConfigModal() {
  document.getElementById('configModal').classList.remove('hidden');
  checkCustomModelVisibility();
}

function closeConfigModal() {
  document.getElementById('configModal').classList.add('hidden');
}

function toggleApiKeyVisibility() {
  const input = document.getElementById('inputApiKey');
  const icon = document.getElementById('apiKeyEyeIcon');
  if (input.type === 'password') {
    input.type = 'text';
    icon.className = 'fa-solid fa-eye-slash text-xs';
  } else {
    input.type = 'password';
    icon.className = 'fa-solid fa-eye text-xs';
  }
}

async function saveAiConfig() {
  const apiKey = (document.getElementById('inputApiKey').value || '').trim();
  const baseUrl = (document.getElementById('inputBaseUrl')?.value || '').trim();
  const selectModel = document.getElementById('selectModel');
  let model = selectModel ? selectModel.value : 'gpt-6-luna';

  if (model === 'custom') {
    const customVal = (document.getElementById('inputCustomModel')?.value || '').trim();
    model = customVal || 'gpt-6-luna';
  }

  const payload = {
    openai_model: model,
    openai_base_url: baseUrl
  };
  if (apiKey) {
    payload.openai_api_key = apiKey;
  }

  try {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al guardar configuración');

    alert('Configuración guardada exitosamente.');
    document.getElementById('inputApiKey').value = '';
    closeConfigModal();
    loadConfig();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

async function testAiConnection() {
  const apiKey = (document.getElementById('inputApiKey').value || '').trim();
  const baseUrl = (document.getElementById('inputBaseUrl')?.value || '').trim();
  const selectModel = document.getElementById('selectModel');
  let model = selectModel ? selectModel.value : 'gpt-6-luna';

  if (model === 'custom') {
    const customVal = (document.getElementById('inputCustomModel')?.value || '').trim();
    model = customVal || 'gpt-6-luna';
  }

  const btn = document.getElementById('btnTestConn');
  const originalHtml = btn.innerHTML;

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Probando...';

  try {
    const res = await fetch('/api/test-openai-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        openai_api_key: apiKey,
        openai_model: model,
        openai_base_url: baseUrl
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Fallo en la conexión');

    alert('✅ ' + data.message);
  } catch (err) {
    alert('❌ ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// -------------------------------------------------------------
// CV DRAG & DROP AND PARSING
// -------------------------------------------------------------

function setupDropZone() {
  const zone = document.getElementById('dropZone');
  const input = document.getElementById('cvFileInput');
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('border-brand-500', 'bg-brand-50/50', 'dark:bg-brand-950/20');
  });

  ['dragleave', 'dragend'].forEach(type => {
    zone.addEventListener(type, () => {
      zone.classList.remove('border-brand-500', 'bg-brand-50/50', 'dark:bg-brand-950/20');
    });
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('border-brand-500', 'bg-brand-50/50', 'dark:bg-brand-950/20');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadCV(e.dataTransfer.files[0]);
    }
  });

  input.addEventListener('change', () => {
    if (input.files && input.files[0]) {
      uploadCV(input.files[0]);
    }
  });
}

async function uploadCV(file) {
  if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
    alert('Por favor selecciona un archivo PDF válido.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const loading = document.getElementById('cvLoading');
  const results = document.getElementById('cvResults');

  loading.classList.remove('hidden');
  results.classList.add('hidden');

  try {
    const res = await fetch('/api/upload-cv', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al procesar CV');

    currentProfile = data;
    const sp = data.profile || data.structured_profile || data;
    renderCandidateFacts(sp, data.personal_details);
    results.classList.remove('hidden');
    alert('✅ CV analizado y Fact Sheet calculado con éxito.');
  } catch (err) {
    alert('Error procesando CV: ' + err.message);
  } finally {
    loading.classList.add('hidden');
  }
}

async function loadCurrentProfile() {
  try {
    const res = await fetch('/api/current-profile');
    if (!res.ok) return;
    const data = await res.json();
    if (data && (data.structured_profile || data.profile || data.full_name)) {
      currentProfile = data;
      const sp = data.structured_profile || data.profile || data;
      renderCandidateFacts(sp, data.personal_details);
      document.getElementById('cvResults').classList.remove('hidden');
    }
  } catch (err) {
    console.error('Error cargando perfil actual:', err);
  }
}

function renderCandidateFacts(profileOrData, personal) {
  if (!profileOrData) return;
  const profile = profileOrData.structured_profile || profileOrData.profile || profileOrData;
  const personalData = personal || profileOrData.personal_details || profile.personal_details || {};

  const candName = profile.full_name || (personalData.first_name ? `${personalData.first_name} ${personalData.last_name || ''}`.trim() : 'Candidato');
  document.getElementById('resCandidateName').textContent = candName;
  document.getElementById('resCandidateHeadline').textContent = profile.headline_or_role || profile.professional_summary || 'Titular Profesional';
  document.getElementById('resTotalYears').textContent = `${profile.total_years_experience || 0} años de experiencia`;

  // Populate dynamic personal inputs
  if (document.getElementById('candFirstName')) document.getElementById('candFirstName').value = personalData.first_name || '';
  if (document.getElementById('candLastName')) document.getElementById('candLastName').value = personalData.last_name || '';
  if (document.getElementById('candEmail')) document.getElementById('candEmail').value = personalData.email || profile.email || '';
  if (document.getElementById('candPhoneCode')) document.getElementById('candPhoneCode').value = personalData.phone_country_code || '+51';
  if (document.getElementById('candPhoneNumber')) document.getElementById('candPhoneNumber').value = personalData.phone_number || profile.phone || '';
  if (document.getElementById('candCity')) document.getElementById('candCity').value = personalData.city || profile.city || 'Lima';
  if (document.getElementById('candCountry')) document.getElementById('candCountry').value = personalData.country || profile.country || 'Perú';

  // 1. Technical Skills Grid
  let skillsList = [];
  if (Array.isArray(profile.skills_with_years) && profile.skills_with_years.length > 0) {
    skillsList = profile.skills_with_years;
  } else if (Array.isArray(profile.skills_inventory) && profile.skills_inventory.length > 0) {
    skillsList = profile.skills_inventory;
  } else if (Array.isArray(profile.skills) && profile.skills.length > 0) {
    skillsList = profile.skills;
  } else if (profile.fact_sheet_skills && typeof profile.fact_sheet_skills === 'object') {
    skillsList = Object.entries(profile.fact_sheet_skills).map(([k, v]) => ({ name: k, years_experience: v }));
  }

  const grid = document.getElementById('skillsGrid');
  grid.innerHTML = '';

  if (skillsList.length === 0) {
    grid.innerHTML = '<p class="text-xs text-slate-400 col-span-full py-2">No se detectaron habilidades específicas en el CV.</p>';
  } else {
    skillsList.forEach(s => {
      let name = '';
      let years = '';
      let proficiency = '';

      if (typeof s === 'string') {
        name = s;
      } else if (typeof s === 'object' && s !== null) {
        name = s.name || s.skill_name || s.skill || Object.keys(s)[0] || '';
        years = s.years_experience !== undefined ? s.years_experience : (s.years !== undefined ? s.years : '');
        proficiency = s.proficiency || s.level || '';
      }

      if (!name) return;

      const card = document.createElement('div');
      card.className = 'p-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs flex justify-between items-center shadow-xs';
      const profBadge = proficiency ? `<span class="text-[9px] uppercase font-bold text-slate-400 block">${escapeHtml(proficiency)}</span>` : '';
      const yearsBadge = (years !== '' && years !== null && years !== undefined)
        ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-100 text-brand-700 dark:bg-brand-900/60 dark:text-brand-300 shrink-0 border border-brand-200 dark:border-brand-800">${years}a</span>`
        : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 shrink-0">✓</span>`;

      card.innerHTML = `
        <div class="truncate pr-1">
          <span class="font-semibold text-slate-800 dark:text-slate-100 truncate block">${escapeHtml(name)}</span>
          ${profBadge}
        </div>
        ${yearsBadge}
      `;
      grid.appendChild(card);
    });
  }

  // 2. Education List
  const eduSec = document.getElementById('educationSection');
  const eduList = document.getElementById('educationList');
  if (eduSec && eduList) {
    const education = profile.education || profile.academic_history || [];
    if (Array.isArray(education) && education.length > 0) {
      eduSec.classList.remove('hidden');
      eduList.innerHTML = '';
      education.forEach(e => {
        let text = typeof e === 'string' ? e : [e.degree || e.title, e.institution || e.university, e.year || e.dates].filter(Boolean).join(' • ');
        if (!text) return;

        const item = document.createElement('div');
        item.className = 'p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs flex items-center gap-2';
        item.innerHTML = `
          <i class="fa-solid fa-graduation-cap text-indigo-500 text-xs"></i>
          <span class="font-medium text-slate-800 dark:text-slate-200">${escapeHtml(text)}</span>
        `;
        eduList.appendChild(item);
      });
    } else {
      eduSec.classList.add('hidden');
    }
  }

  // 3. Certifications List
  const certSec = document.getElementById('certificationsSection');
  const certList = document.getElementById('certificationsList');
  if (certSec && certList) {
    const certs = profile.certifications || profile.certificates || [];
    if (Array.isArray(certs) && certs.length > 0) {
      certSec.classList.remove('hidden');
      certList.innerHTML = '';
      certs.forEach(c => {
        let text = typeof c === 'string' ? c : [c.name || c.title, c.issuer, c.year].filter(Boolean).join(' • ');
        if (!text) return;

        const item = document.createElement('div');
        item.className = 'p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs flex items-center gap-2';
        item.innerHTML = `
          <i class="fa-solid fa-certificate text-amber-500 text-xs"></i>
          <span class="font-medium text-slate-800 dark:text-slate-200">${escapeHtml(text)}</span>
        `;
        certList.appendChild(item);
      });
    } else {
      certSec.classList.add('hidden');
    }
  }

  // 4. Languages List
  const langSec = document.getElementById('languagesSection');
  const langList = document.getElementById('languagesList');
  if (langSec && langList) {
    const langs = profile.languages || [];
    if (Array.isArray(langs) && langs.length > 0) {
      langSec.classList.remove('hidden');
      langList.innerHTML = '';
      langs.forEach(l => {
        let name = typeof l === 'string' ? l : `${l.language} (${l.proficiency || ''})`;
        if (!name) return;

        const pill = document.createElement('span');
        pill.className = 'px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1';
        pill.innerHTML = `<i class="fa-solid fa-check text-[10px]"></i> ${escapeHtml(name)}`;
        langList.appendChild(pill);
      });
    } else {
      langSec.classList.add('hidden');
    }
  }
}

async function saveCandidateDetails() {
  const payload = {
    first_name: document.getElementById('candFirstName').value.trim(),
    last_name: document.getElementById('candLastName').value.trim(),
    email: document.getElementById('candEmail').value.trim(),
    phone_country_code: document.getElementById('candPhoneCode').value.trim(),
    phone_number: document.getElementById('candPhoneNumber').value.trim(),
    city: document.getElementById('candCity').value.trim() || 'Lima',
    country: document.getElementById('candCountry').value.trim() || 'Perú'
  };

  try {
    const res = await fetch('/api/candidate-details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Error al guardar datos personales');
    alert('✅ Datos del candidato guardados.');
    loadCurrentProfile();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// -------------------------------------------------------------
// LINKEDIN JOB SEARCH
// -------------------------------------------------------------

async function triggerJobSearch() {
  const btn = document.getElementById('btnSearchJobs');
  const loading = document.getElementById('searchLoading');
  const originalHtml = btn.innerHTML;

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Buscando...';
  loading.classList.remove('hidden');

  const modalities = [];
  if (document.getElementById('modRemote').checked) modalities.push('REMOTE');
  if (document.getElementById('modHybrid').checked) modalities.push('HYBRID');
  if (document.getElementById('modOnsite').checked) modalities.push('ON_SITE');

  const payload = {
    keywords: document.getElementById('searchKeywords').value.trim() || 'Software Engineer',
    location: document.getElementById('searchLocation').value.trim() || 'Lima, Perú',
    date_range: document.getElementById('searchDateRange').value,
    limit: parseInt(document.getElementById('searchLimit').value, 10) || 25,
    easy_apply_only: document.getElementById('filterEasyApply').checked,
    modalities: modalities
  };

  try {
    const res = await fetch('/api/search-jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error en la búsqueda');

    savedJobs = data.jobs || [];
    renderJobsList(savedJobs);
    alert(`✅ Búsqueda completada. Se encontraron ${savedJobs.length} vacantes activas en LinkedIn.`);
  } catch (err) {
    alert('Error en búsqueda de LinkedIn: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    loading.classList.add('hidden');
  }
}

async function loadSavedJobs() {
  try {
    const res = await fetch('/api/saved-jobs');
    if (!res.ok) return;
    const data = await res.json();
    if (Array.isArray(data)) {
      savedJobs = data;
      renderJobsList(savedJobs);
    }
  } catch (err) {
    console.error('Error cargando vacantes guardadas:', err);
  }
}

function renderJobsList(jobs) {
  const container = document.getElementById('jobsList');
  const countTitle = document.getElementById('jobsCountTitle');
  if (countTitle) countTitle.textContent = `Vacantes Encontradas (${jobs.length})`;

  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<p class="text-xs text-slate-400 py-6 text-center">No se encontraron ofertas activas con los filtros seleccionados.</p>';
    return;
  }

  container.innerHTML = '';
  jobs.forEach((job, idx) => {
    const card = document.createElement('div');
    card.className = 'p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs hover:border-brand-500 transition';

    const easyBadge = job.is_easy_apply
      ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"><i class="fa-solid fa-bolt"></i> Easy Apply</span>`
      : `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">${escapeHtml(job.destination_portal || 'Sitio Empresa')}</span>`;

    const btnId = `btn-tailor-s-${job.job_id || idx}`;
    card.innerHTML = `
      <div class="space-y-1">
        <div class="flex items-center gap-1.5">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
            <i class="fa-brands fa-linkedin"></i> LinkedIn
          </span>
          ${easyBadge}
        </div>
        <h4 class="text-xs font-bold text-slate-900 dark:text-white">${escapeHtml(job.title)}</h4>
        <p class="text-[11px] text-slate-500">${escapeHtml(job.company)} • ${escapeHtml(job.location)} • ${escapeHtml(job.date_posted || 'Reciente')}</p>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <button id="${btnId}" onclick="generateTailoredCV('${job.job_id}', '${encodeURIComponent(job.title)}', '${encodeURIComponent(job.company)}', '${btnId}')" class="px-3 py-1.5 rounded-lg border border-emerald-600 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-xs font-semibold flex items-center gap-1.5 transition">
          <i class="fa-solid fa-file-pdf"></i> Generar CV ATS
        </button>
        <a href="${job.url}" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition">
          Ver en LinkedIn <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
      </div>
    `;
    container.appendChild(card);
  });
}

// -------------------------------------------------------------
// MATCHING & HARVARD ATS CV GENERATION
// -------------------------------------------------------------

async function triggerEvaluateMatches() {
  const btn = document.getElementById('btnEvalMatches');
  const loading = document.getElementById('matchesLoading');
  const originalHtml = btn.innerHTML;

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Evaluando...';
  loading.classList.remove('hidden');

  try {
    const res = await fetch('/api/evaluate-matches', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error evaluando vacantes');

    savedMatches = data.matches || [];
    renderMatchesList(savedMatches);
    alert(`✅ Evaluación completada. Se evaluaron ${savedMatches.length} puestos con Inteligencia Artificial.`);
  } catch (err) {
    alert('Error al evaluar afinidad: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    loading.classList.add('hidden');
  }
}

async function loadSavedMatches() {
  try {
    const res = await fetch('/api/saved-matches');
    if (!res.ok) return;
    const data = await res.json();
    if (Array.isArray(data)) {
      savedMatches = data;
      renderMatchesList(savedMatches);
    }
  } catch (err) {
    console.error('Error cargando evaluaciones:', err);
  }
}

function renderMatchesList(matches) {
  const container = document.getElementById('matchesList');
  if (!matches || matches.length === 0) {
    container.innerHTML = '<p class="text-xs text-slate-400 py-6 text-center">No hay vacantes evaluadas aún. Haz clic en "Evaluar con IA".</p>';
    return;
  }

  container.innerHTML = '';
  matches.forEach((job, idx) => {
    const dec = job.evaluation || {};
    const score = dec.match_score || 0;
    let badgeClass = 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300';
    if (score >= 80) badgeClass = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300';
    else if (score >= 65) badgeClass = 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300';

    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-2.5 shadow-xs';

    const strengths = (dec.matching_points || []).map(p => `<li class="flex items-center gap-1.5"><i class="fa-solid fa-check text-emerald-500 text-[10px]"></i> ${escapeHtml(p)}</li>`).join('');
    const gaps = (dec.missing_gaps || []).map(g => `<li class="flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation text-amber-500 text-[10px]"></i> ${escapeHtml(g)}</li>`).join('');

    const btnId = `btn-tailor-m-${job.job_id || idx}`;
    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold ${badgeClass}">${score}% MATCH</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">${escapeHtml(dec.recommendation || 'REVIEW')}</span>
          </div>
          <h3 class="text-sm font-bold text-slate-900 dark:text-white">${escapeHtml(job.title)}</h3>
          <p class="text-xs text-slate-500">${escapeHtml(job.company)} • ${escapeHtml(job.location)}</p>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <button id="${btnId}" onclick="generateTailoredCV('${job.job_id}', '${encodeURIComponent(job.title)}', '${encodeURIComponent(job.company)}', '${btnId}')" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 transition shadow-sm">
            <i class="fa-solid fa-file-pdf"></i> Generar CV ATS
          </button>
          <a href="${job.url}" target="_blank" class="px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold hover:border-brand-500 transition flex items-center gap-1">
            Postular <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>
      </div>

      <p class="text-xs text-slate-600 dark:text-slate-300 italic">${escapeHtml(dec.brief_rationale || '')}</p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] pt-1 border-t border-slate-100 dark:border-slate-700">
        <div>
          <span class="font-bold text-emerald-700 dark:text-emerald-400 block mb-0.5">Puntos Fuertes:</span>
          <ul class="space-y-0.5 text-slate-600 dark:text-slate-300">${strengths || '<li>No se detectaron fortalezas clave.</li>'}</ul>
        </div>
        <div>
          <span class="font-bold text-amber-700 dark:text-amber-400 block mb-0.5">Brechas / Gaps:</span>
          <ul class="space-y-0.5 text-slate-600 dark:text-slate-300">${gaps || '<li>Cumple con todos los requisitos.</li>'}</ul>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Generate Tailored Harvard ATS CV
async function generateTailoredCV(jobId, titleEnc, compEnc, btnId) {
  const btn = document.getElementById(btnId);
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i> Adaptando Harvard ATS...';
  }

  const title = decodeURIComponent(titleEnc || '');
  const company = decodeURIComponent(compEnc || '');

  try {
    const res = await fetch('/api/generate-tailored-cv', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: jobId,
        title: title,
        company: company
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al generar CV adaptado');

    // Populate Tailored Modal
    const tailored = data.tailored_data || {};
    document.getElementById('tailorTargetHeadline').textContent = tailored.target_headline || title;
    document.getElementById('tailorSummary').textContent = tailored.professional_summary || '';

    const skillsDiv = document.getElementById('tailorSkills');
    skillsDiv.innerHTML = '';
    (tailored.core_competencies || []).forEach(s => {
      const sp = document.createElement('span');
      sp.className = 'px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300';
      sp.textContent = s;
      skillsDiv.appendChild(sp);
    });

    const dlBtn = document.getElementById('tailorDownloadBtn');
    dlBtn.href = data.download_url;
    dlBtn.setAttribute('download', data.filename);

    document.getElementById('tailoredModal').classList.remove('hidden');

    if (btn) {
      btn.outerHTML = `
        <a href="${data.download_url}" download="${data.filename}" class="px-3 py-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-300 text-xs font-semibold flex items-center gap-1.5 hover:bg-emerald-200 transition">
          <i class="fa-solid fa-file-arrow-down"></i> Descargar ATS
        </a>
      `;
    }
  } catch (err) {
    alert('Error al adaptar CV: ' + err.message);
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  }
}

function closeTailoredModal() {
  document.getElementById('tailoredModal').classList.add('hidden');
}

// -------------------------------------------------------------
// CLEAR ALL DATA
// -------------------------------------------------------------

async function clearAllData() {
  if (!confirm('¿Deseas eliminar todos los registros de búsqueda, matches y el CV cargado?')) {
    return;
  }

  try {
    const res = await fetch('/api/clear-all-data', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al limpiar datos');

    currentProfile = null;
    savedJobs = [];
    savedMatches = [];

    document.getElementById('cvResults').classList.add('hidden');
    document.getElementById('candFirstName').value = '';
    document.getElementById('candLastName').value = '';
    document.getElementById('candEmail').value = '';
    document.getElementById('candPhoneNumber').value = '';
    document.getElementById('skillsGrid').innerHTML = '';
    renderJobsList([]);
    renderMatchesList([]);

    alert('✅ ' + data.message);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// Helper: Escape HTML string
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
