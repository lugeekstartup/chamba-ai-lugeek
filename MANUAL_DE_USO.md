# 📘 Manual de Uso Oficial — Chamba AI Lugeek
### *Búsqueda de trabajo eficaz con la IA*
**Repositorio Oficial:** [https://github.com/lugeekstartup](https://github.com/lugeekstartup)  
**Versión:** 1.0.0 — Edición Comunitaria Open Source  

---

## 📑 Tabla de Contenidos
1. [Introducción](#1-introducción)
2. [Requisitos del Sistema](#2-requisitos-del-sistema)
3. [Instalación y Puesta en Marcha](#3-instalación-y-puesta-en-marcha)
4. [Configuración de Inteligencia Artificial (Familia Luna 6 / OpenAI)](#4-configuración-de-inteligencia-artificial)
5. [Guía Paso a Paso de Uso](#5-guía-paso-a-paso-de-uso)
   - [Paso 1: Carga y Análisis Inteligente del CV](#paso-1-carga-y-análisis-inteligente-del-cv)
   - [Paso 2: Búsqueda de Empleos en Tiempo Real en LinkedIn](#paso-2-búsqueda-de-empleos-en-tiempo-real-en-linkedin)
   - [Paso 3: Evaluación Semántica y Matching Cognitivo](#paso-3-evaluación-semántica-y-matching-cognitivo)
   - [Paso 4: Generación y Descarga de CV ATS Estándar Harvard](#paso-4-generación-y-descarga-de-cv-ats-estándar-harvard)
6. [Resolución de Problemas Comunes (FAQ)](#6-resolución-de-problemas-comunes-faq)
7. [Seguridad y Privacidad](#7-seguridad-y-privacidad)

---

## 1. Introducción

**Chamba AI Lugeek** es una plataforma autónoma de búsqueda de empleo diseñada para maximizar las probabilidades de éxito de los postulantes profesionales. Integra técnicas modernas de web scraping sin inicio de sesión, procesamiento de lenguaje natural y motores de maquetación tipográfica bajo el riguroso **Estándar Harvard**.

### ¿Qué hace diferente a Chamba AI Lugeek?
- **Zero Login Scraping:** Extrae ofertas públicas en tiempo real directamente de LinkedIn sin requerir usuario ni contraseñas.
- **Fact Sheet Inmutable de Habilidades:** Cuantifica los años reales demostrables de experiencia para cada tecnología y framework.
- **Compatible con la Familia Luna 6 y OpenAI:** Permite especificar URLs de endpoints personalizados o gateways de IA.
- **Normativa Harvard Estricta:** Genera un CV en PDF 100% monocromático negro, optimizado para sistemas ATS corporativos y garantizado estrictamente en un máximo de **2 páginas**.

---

## 2. Requisitos del Sistema

- **Sistema Operativo:** Windows 10/11, Linux (Ubuntu, Debian, Fedora) o macOS.
- **Python:** Versión 3.10 o superior instalada.
- **Navegador Web:** Google Chrome, Microsoft Edge, Mozilla Firefox o Brave.
- **Conexión a Internet:** Para scraping de LinkedIn y consultas al proveedor de IA.

---

## 3. Instalación y Puesta en Marcha

### En Windows (1 Clic):
En la carpeta raíz del proyecto encontrarás el archivo ejecutable por lotes:
```text
INICIAR_APP.bat
```
1. Haz doble clic sobre **`INICIAR_APP.bat`**.
2. El script detectará tu instalación de Python, configurará el entorno virtual (`venv`), descargará las dependencias y el motor Chromium de Playwright.
3. Se abrirá automáticamente la ventana de tu navegador en:
   **`http://localhost:8000`**

### Instalación Manual (Linux / macOS / Consola):
```bash
# 1. Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate    # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt
playwright install chromium

# 3. Iniciar el servidor web
python run_server.py
```

---

## 4. Configuración de Inteligencia Artificial

Para activar la extracción de CV, el matching semántico y la generación de CV ATS, debes conectar tu proveedor de IA.

1. En la esquina superior derecha de la aplicación, haz clic en el botón **Configurar IA** (o en el banner de advertencia).
2. Se abrirá el modal de **Configuración de Inteligencia Artificial**:

```
+-----------------------------------------------------------------------+
|  Configuración de Inteligencia Artificial                           X |
+-----------------------------------------------------------------------+
|  URL de la API (Base URL / Endpoint)                                  |
|  [ https://api.tu-proveedor.com/v1                                  ] |
|  * Si usas la Familia Luna 6 o un gateway propio, ingresa la URL web. |
|  * Si usas OpenAI oficial directo, puedes dejar este campo vacío.     |
|                                                                       |
|  API Key / Clave de Acceso                                            |
|  [ sk-Md10a...................................b2b9                  ] |
|                                                                       |
|  Modelo de Inteligencia Artificial                                    |
|  [ Familia Luna 6: gpt-6-luna (Recomendado)                         v ] |
|    - gpt-6-luna (Luna 6 Estándar)                                     |
|    - gpt-6-luna-pro (Luna 6 Pro — Máxima Capacidad)                   |
|    - gpt-6-luna-mini (Luna 6 Mini — Ultra Rápido)                     |
|    - gpt-4o (OpenAI Oficial)                                          |
|    - gpt-4o-mini (OpenAI Oficial)                                     |
|    - Otro modelo personalizado...                                     |
+-----------------------------------------------------------------------+
|  [ Probar Conexión ]                            [ Guardar Cambios ]   |
+-----------------------------------------------------------------------+
```

### Explicación de los Campos:
- **URL de la API (Base URL):**
  - **¿Tienes un proveedor web o gateway con la Familia Luna 6?** Ingresa la URL de dicho servicio (ejemplo: `https://api.tu-proveedor.com/v1`).
  - **¿Usas OpenAI oficial?** Déjalo en blanco o escribe `https://api.openai.com/v1`.
- **API Key:** Ingresa la clave secreta proporcionada por tu proveedor (ejemplo: `sk-...`).
- **Modelo:** Selecciona `gpt-6-luna` (predeterminado) o el modelo correspondiente a tu plan.

> [!TIP]
> Haz clic en **Probar Conexión** antes de guardar. El sistema enviará un mensaje de comprobación de baja latencia al endpoint especificado y confirmará si la clave y el modelo responden correctamente. Luego haz clic en **Guardar Cambios**.

---

## 5. Guía Paso a Paso de Uso

### Paso 1: Carga y Análisis Inteligente del CV
1. Ve a la pestaña **1. Mi Perfil & CV**.
2. Arrastra tu archivo de CV en formato PDF (máximo 10 MB) al recuadro punteado o haz clic en **Seleccionar Archivo PDF**.
3. El motor de IA analizará tu trayectoria y extraerá:
   - **Datos Personales:** Nombre, Apellidos, Correo, Teléfono (con código de país) y Ubicación (predeterminada a **Lima, Perú**).
   - **Fact Sheet de Habilidades Técnicas:** Años reales acumulados en cada lenguaje, framework, base de datos y herramienta.
   - **Educación:** Grados universitarios, maestrías y diplomados con su año e institución.
   - **Certificaciones Oficiales:** Licencias y diplomas profesionales detectados.
   - **Idiomas:** Lenguas y nivel de competencia (Nativo, C1, B2, etc.).
4. Si deseas corregir algún dato de contacto, puedes editar los campos y hacer clic en **Guardar Datos Personales**.

---

### Paso 2: Búsqueda de Empleos en Tiempo Real en LinkedIn
1. Ve a la pestaña **2. Búsqueda en LinkedIn**.
2. Completa los criterios de búsqueda:
   - **Cargo o Palabras Clave:** Ej: `Software Engineer`, `Full Stack Developer`, `Data Engineer`, `Tech Lead`.
   - **Ubicación:** Predefinido en `Lima, Perú` (puedes cambiarlo a cualquier ciudad o país, o buscar globalmente).
   - **Modalidad:** Selecciona entre **Remoto**, **Híbrido** y/o **Presencial**.
   - **Filtro Easy Apply:** Activa la casilla para priorizar vacantes con solicitud sencilla directa.
   - **Fecha de publicación:** Último mes, última semana o últimas 24 horas.
3. Haz clic en **Buscar Empleos**.
4. Chamba AI consultará LinkedIn mediante scraping resiliente y mostrará la lista con:
   - Título del puesto y Empresa.
   - Ubicación y Modalidad.
   - Portal de destino identificado (LinkedIn, Workday, Lever, Greenhouse, etc.).
   - Validación de disponibilidad (se descartan enlaces obsoletos o eliminados).

---

### Paso 3: Evaluación Semántica y Matching Cognitivo
1. Ve a la pestaña **3. Matching & CV ATS**.
2. Haz clic en el botón **Evaluar con IA**.
3. El motor cognitivo contrastará las ofertas encontradas contra el Fact Sheet de tu CV y presentará un tablero ordenado por compatibilidad:
   - **Score de Compatibilidad (0% - 100%):** Nivel de ajuste del candidato.
   - **Recomendación Ejecutiva:**
     - 🟢 **APPLY (Score ≥ 80%):** Postulación altamente recomendada.
     - 🟡 **MANUAL_REVIEW (65% – 79%):** Revisar requisitos particulares antes de enviar.
     - 🔴 **DISCARD (< 65%):** Poca afinidad o faltan tecnologías esenciales.
   - **Fortalezas del Perfil:** Qué habilidades de tu CV respaldan la postulación.
   - **Gaps / Brechas:** Requisitos específicos solicitados por la vacante que no figuran en tu CV.

---

### Paso 4: Generación y Descarga de CV ATS Estándar Harvard
1. En la lista de puestos evaluados del Paso 3, localiza la vacante a la que deseas postularte.
2. Haz clic en el botón **Generar CV ATS**.
3. En pocos segundos, Chamba AI adaptará tu perfil a la descripción del puesto y presentará una ventana con:
   - **Titular Estratégico Alineado.**
   - **Resumen Profesional ATS** con palabras clave exactas.
   - **Competencias Técnicas Inyectadas.**
4. Haz clic en **Descargar PDF Harvard (ATS)**.
5. Se descargará un archivo PDF profesional que cumple con:
   - **Monocromático 100% negro (`#000000`):** Sin colores, barras de progreso ni elementos visuales que confundan a los lectores ATS corporativos.
   - **Límite físico estricto de hasta 2 páginas:** Ni una sola línea desbordada a una tercera página.
   - **Tipografía Serif Harvard:** Estructura académica limpia, viñetas de logros cuantificables y jerarquía visual impecable.

---

## 6. Resolución de Problemas Comunes (FAQ)

### ¿Por qué obtengo el error "401 - Incorrect API key provided"?
- **Causa:** El sistema estaba enviando tu clave al endpoint oficial de OpenAI (`api.openai.com`), pero tu API Key pertenece a un proveedor web de la Familia Luna 6 o un gateway privado.
- **Solución:** Abre **Configurar IA**, escribe la **URL de la API (Base URL)** provista por tu servicio (ejemplo: `https://api.tu-proveedor.com/v1`), selecciona el modelo `gpt-6-luna` y presiona **Probar Conexión**.

### ¿Puedo usar la aplicación sin ingresar ninguna API Key?
- **Sí.** La funcionalidad del **Paso 2 (Búsqueda y Scraping en LinkedIn)** funciona al 100% sin necesidad de API Key ni inicio de sesión. Solo requieres la API Key para el análisis de CV, scoring semántico y creación del PDF Harvard.

### ¿Dónde se guardan mis datos y mi CV?
- Todos los datos se almacenan exclusivamente en tu computadora local, dentro de la carpeta `data/` del proyecto. No se envía información a bases de datos en la nube de Lugeek.

### ¿Cómo limpio todos los datos guardados para empezar de cero?
- Haz clic en el icono de la **Papelera** en la barra superior. Esto eliminará de inmediato el CV analizado, las vacantes guardadas y los PDFs temporales.

---

## 7. Seguridad y Privacidad

- **Código Abierto y Transparente:** Todo el código fuente de los endpoints y scrapers es auditable en la carpeta `core/` y `web/`.
- **Credenciales Aisladas:** Tu clave API se guarda en `config/settings.json`, archivo que está protegido por `.gitignore` para prevenir fugas accidentales al compartir código.
- **Sin Cookies de Navegación Requeridas:** No necesitas entregar tus credenciales de LinkedIn ni cookies de sesión.

---

## 🏢 Créditos y Soporte
Desarrollado y mantenido por **Lugeek Startup**.  
Visita y colabora en nuestro repositorio oficial de GitHub:  
👉 **[https://github.com/lugeekstartup](https://github.com/lugeekstartup)**
