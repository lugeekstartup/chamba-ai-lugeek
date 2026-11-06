# 💼 Chamba AI Lugeek

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-PDF%20Engine-2EAD33.svg)](https://playwright.dev/python/)
[![GitHub](https://img.shields.io/badge/GitHub-lugeekstartup-181717.svg?logo=github)](https://github.com/lugeekstartup)

> **Búsqueda de trabajo eficaz con la IA — Agente Autónomo de Búsqueda de Empleos en LinkedIn, Extracción Inteligente de CV y Generador de Resumes ATS Harvard.**

Chamba AI Lugeek es una solución open-source desarrollada para que cualquier profesional o desarrollador pueda automatizar su búsqueda de trabajo, evaluar vacantes en LinkedIn en tiempo real y generar versiones adaptadas de su CV en formato ATS Harvard optimizadas para superar los filtros de selección corporativa.

Compatible con la **Familia Luna 6** (`gpt-6-luna`, `gpt-6-luna-pro`, `gpt-6-luna-mini`), gateways personalizados y los modelos oficiales de OpenAI (`gpt-4o`, `gpt-4o-mini`).

---

## 📖 Manual de Uso Completo
Para una guía paso a paso ilustrada con explicaciones detalladas de cada funcionalidad, consulta el archivo [MANUAL_DE_USO.md](MANUAL_DE_USO.md).

---

## ✨ Características Principales

1. **Scraping Público y Resiliente en LinkedIn (Sin Login):**
   - Emplea `curl_cffi` con impersonación TLS de Chrome para extraer ofertas sin requerir credenciales ni navegadores pesados en segundo plano.
   - Filtro estricto para vacantes con **Easy Apply (Solicitud sencilla)**.
   - Detección automática y eliminación de publicaciones cerradas o expiradas (HTTP 404, 410 o avisos de cierre).
   - Identificación inteligente del portal de destino (Workday, Lever, Greenhouse, SmartRecruiters, etc.).
   - **¡El scraping funciona inmediatamente sin necesidad de API Key!**

2. **Extracción y Fact Sheet Inmutable de CV con IA:**
   - Carga cualquier CV en PDF (hasta 10 MB).
   - Extrae automáticamente los años reales acumulados de experiencia técnica por cada herramienta, framework y lenguaje.
   - Organiza la formación académica, certificaciones profesionales oficiales e idiomas.
   - Normaliza automáticamente la ubicación por defecto a Lima / Perú o cualquier ciudad del mundo.

3. **Matching Cognitivo & Análisis de Brechas (Gaps):**
   - Evalúa cada oferta laboral con Inteligencia Artificial frente a tu Fact Sheet.
   - Asigna un puntaje de afinidad (0–100%), recomendación ejecutiva (`APPLY`, `MANUAL_REVIEW`, `DISCARD`), fortalezas clave y habilidades faltantes.

4. **Generador de CV ATS bajo Estándar Harvard Oficial:**
   - **100% Monocromático Negro (`#000000`):** Cero adornos gráficos, sin barras de progreso, iconos confusos ni pills coloreadas que bloqueen los parsers ATS corporativos.
   - **Límite Estricto de 2 Páginas:** Diseñado con presupuestos tipográficos precisos para garantizar que el archivo PDF resultante nunca exceda 2 páginas.
   - **Tipografía Serif Clásica:** Times New Roman / Georgia con formato Harvard (títulos en mayúsculas, líneas divisorias negras sólidas de 1px y fechas alineadas a la derecha).
   - **Categorización Textual de Habilidades:** Agrupación limpia en texto corrido (*Lenguajes & Frameworks*, *Cloud & DevOps*, *Bases de Datos*, etc.).
   - **Inyección de Palabras Clave ATS:** Adapta la experiencia real del postulante resaltando los términos clave solicitados en la vacante.

5. **Configuración 100% en la Interfaz Web (URL Base & Familia Luna 6):**
   - Soporte para configurar una **URL Base de API personalizada (Endpoint)** para conectar con tu proveedor web o gateway de IA.
   - Soporte nativo para la **Familia Luna 6** (`gpt-6-luna`, `gpt-6-luna-pro`, `gpt-6-luna-mini`) y modelos OpenAI.
   - Tu clave se almacena exclusivamente en tu máquina local (`config/settings.json`) y **nunca** se comparte con terceros.

---

## 🚀 Inicio Rápido (Quick Start)

### Opción A: En Windows con 1 Clic
Simplemente haz doble clic en el archivo:
```bat
INICIAR_APP.bat
```
El script creará automáticamente el entorno virtual `venv`, instalará los paquetes y abrirá el servidor en `http://localhost:8000`.

---

### Opción B: Instalación Manual con Python

#### 1. Clonar el repositorio
```bash
git clone https://github.com/lugeekstartup/chamba-ai-lugeek.git
cd chamba-ai-lugeek
```

#### 2. Crear entorno virtual e instalar dependencias
```bash
# En Windows:
python -m venv venv
venv\Scripts\activate

# En Linux/macOS:
python3 -m venv venv
source venv/bin/activate

# Instalar requerimientos
pip install -r requirements.txt
playwright install chromium
```

#### 3. Ejecutar la aplicación
```bash
python run_server.py
```
Abre tu navegador web en: **`http://localhost:8000`**

---

### Opción C: Ejecución con Docker
```bash
docker build -t chamba-ai-lugeek .
docker run -p 8000:8000 chamba-ai-lugeek
```

---

## 🛠️ Configuración de la API (Familia Luna 6 / OpenAI)

Para activar las funciones avanzadas de lectura de CV, matching semántico y generación de CV ATS:
1. Abre la aplicación en tu navegador (`http://localhost:8000`).
2. Haz clic en el botón **Configurar IA** en la barra superior derecha.
3. Si utilizas un proveedor web con la **Familia Luna 6** o un gateway personalizado, ingresa su URL en el campo **URL de la API (Base URL)** (ejemplo: `https://tu-proveedor.com/v1`). Si usas OpenAI oficial, déjalo vacío o usa `https://api.openai.com/v1`.
4. Pega tu `API Key` (comienza con `sk-...`).
5. Selecciona el modelo deseado (`gpt-6-luna`, `gpt-6-luna-pro`, `gpt-6-luna-mini`, `gpt-4o`, etc.).
6. Haz clic en **Probar Conexión** y luego en **Guardar Cambios**.

---

## 📂 Estructura del Proyecto

```
chamba_ai_community/
├── core/
│   ├── linkedin_scraper.py   # Scraper público con curl_cffi y filtros anti-bot
│   ├── cv_parser.py          # Extracción estructurada de CV y Fact Sheet
│   ├── matching_engine.py    # Evaluación cognitiva de afinidad y score
│   ├── cv_tailor.py          # Motor de CV ATS monocromático estándar Harvard
│   └── easy_apply_rpa.py     # Automatización asistida con Playwright
├── web/
│   ├── server.py             # API REST con FastAPI (sin login ni dependencias externas)
│   └── static/
│       ├── index.html        # Interfaz web responsiva con Tailwind CSS y Dark Mode
│       ├── app.js            # Lógica cliente y conexión con APIs
│       └── logo.png          # Logotipo oficial de Lugeek
├── config/
│   └── settings.example.json # Plantilla de configuración local
├── data/                     # Almacenamiento local de CVs y resultados (ignorado en git)
├── Dockerfile                # Despliegue en contenedores
├── INICIAR_APP.bat           # Lanzador rápido para Windows
├── MANUAL_DE_USO.md          # Manual de uso detallado paso a paso
├── requirements.txt          # Dependencias de Python
└── run_server.py             # Script de entrada de Uvicorn
```

---

## 🛡️ Privacidad y Seguridad

- **Sin Servidores Centrales:** Corre 100% en tu máquina local.
- **Sin Base de Datos Externa:** No requiere PostgreSQL ni credenciales externas. Todos los datos se guardan en archivos JSON locales dentro de la carpeta `data/`.
- **Botón de Limpieza Total:** Puedes borrar todo tu historial y datos cargados en cualquier momento con el botón de la papelera en la barra superior.

---

## 🌐 Comunidad y Repositorio Oficial

- **GitHub Oficial:** [https://github.com/lugeekstartup](https://github.com/lugeekstartup)
- **Licencia:** [MIT](LICENSE)
