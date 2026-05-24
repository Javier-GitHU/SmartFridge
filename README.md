<div align="center">

# 🥕 Smart Fridge AI

**Tu chef personal con visión por ordenador**

Sistema inteligente que combina **visión artificial**, **Big Data** e **IA generativa**
para detectar ingredientes en tu nevera y proponerte recetas adaptadas a lo que tienes.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-7B68EE)](https://github.com/ultralytics/ultralytics)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Apache%20Spark](https://img.shields.io/badge/Apache%20Spark-4.1-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache%20NiFi](https://img.shields.io/badge/Apache%20NiFi-2.9-728E9B?logo=apache&logoColor=white)](https://nifi.apache.org/)
[![n8n](https://img.shields.io/badge/n8n-LangChain-EA4B71?logo=n8n&logoColor=white)](https://n8n.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com/)

</div>

---

## 👥 Autores

| | |
|---|---|
| **Alejandro Hortal Valor** | [@alHortalV](https://github.com/alHortalV) |
| **Javier Castro Rodríguez** | [@Javier-GitHU](https://github.com/Javier-GitHU) |

> Proyecto final del **Curso de Especialización en Inteligencia Artificial y Big Data** del **IES Zaidín Vergeles** (Granada, 2025/2026).

---

## 📖 Índice

1. [Descripción](#-descripción)
2. [Características](#-características)
3. [Arquitectura](#-arquitectura)
4. [Estructura del repositorio](#-estructura-del-repositorio)
5. [Stack tecnológico](#-stack-tecnológico)
6. [Requisitos previos](#-requisitos-previos)
7. [Instalación](#-instalación)
8. [Configuración](#%EF%B8%8F-configuración)
9. [Puesta en marcha](#-puesta-en-marcha)
10. [Endpoints de la API](#-endpoints-de-la-api)
11. [Esquema de datos en MongoDB](#-esquema-de-datos-en-mongodb)
12. [Flujo de n8n](#-flujo-de-n8n-chef-cucharón)
15. [Licencia](#-licencia)

---

## 📌 Descripción

**Smart Fridge AI** es una plataforma que resuelve dos problemas cotidianos en cualquier cocina:

- 🕳️ **La "caja negra" de la nevera** — los ingredientes se quedan al fondo, se olvidan y acaban caducando.
- 🤯 **La fatiga de decisión** — pensar qué cocinar con "lo que queda" es agotador.

El sistema combina un **modelo YOLOv8** que reconoce ingredientes en fotos del interior de la nevera, una **API de recetas reales** (Spoonacular) y un **agente conversacional** con personalidad de chef (**Chef Cucharón**, basado en `gpt-4o-mini`) que adapta esas recetas al español, evita repeticiones entre interacciones y propone alternativas creativas.

Paralelamente, el proyecto simula una **arquitectura de Big Data** completa generando telemetría sintética de neveras inteligentes (temperatura, estado de puerta), ingiriéndola con **Apache NiFi**, persistiéndola en **MongoDB** y procesándola con **Apache Spark** para calcular medias y detectar anomalías (picos de temperatura, cadena de frío rota, etc.).

---

## ✨ Características

- 🔍 **Detección de ingredientes** sobre imágenes con YOLOv8 reentrenado (>75 % de accuracy).
- 🍳 **Generación de recetas** combinando Spoonacular + GPT‑4o‑mini con el agente *Chef Cucharón*.
- 💬 **Chat conversacional** con memoria de sesión (`contextWindowLength = 10`).
- 📈 **Simulación IoT**: generación continua de JSONs de 100 neveras virtuales.
- 🔄 **Pipeline NiFi**: ingesta automática de JSONs a MongoDB.
- ⚡ **Procesamiento Spark**: medias de temperatura y detección de anomalías (>10 °C).
- 🖼️ **Almacenamiento de imágenes** en MongoDB usando **GridFS**.
- 🌐 **API REST** ligera con FastAPI y CORS abierto para el frontend.

---

## 🏗️ Arquitectura

El sistema se compone de **dos flujos paralelos** que convergen en MongoDB.

### Flujo Big Data

```
┌──────────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│ generator.py │───▶│   /data   │───▶│  Apache NiFi │───▶│  smartfridge │───▶│   Apache    │
│ (100 fridges)│    │  *.json   │    │   GetFile +  │    │   .raw_data  │    │    Spark    │
│  cada 5 s    │    │           │    │ PutMongoRec. │    │              │    │ (medias +   │
└──────────────┘    └───────────┘    └──────────────┘    └──────┬───────┘    │  anomalías) │
                                                                │             └──────┬──────┘
                                                                ▼                    ▼
                                                       (lectura para Spark)   processed_data
                                                                              + alerts
```

### Flujo de Inteligencia Artificial

```
┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────┐   ┌───────────────────────────┐   ┌──────────┐
│ Usuario │──▶│ Frontend │──▶│  FastAPI     │──▶│ YOLOv8  │──▶│ n8n (Webhook + Spoonacular│──▶│ MongoDB  │
│         │   │   HTML   │   │   /chat      │   │  best.pt│   │ + AI Chef Agent GPT-4o-mi.│   │ recipes  │
└─────────┘   └──────────┘   └──────────────┘   └─────────┘   └───────────────────────────┘   └──────────┘
                                    │                                       │
                                    └──────────── GridFS ──────────────────▶│
                                                                        (fs.files + fs.chunks)
```

---

## 📁 Estructura del repositorio

```
SmartFridge/
├── FastAPI.py          # API REST: detección YOLO + puente a n8n + persistencia
├── generator.py        # Generador de telemetría JSON de neveras virtuales
├── spark_job.py        # Job PySpark: medias por nevera y detección de anomalías
├── NiFi_Flow.json      # Flujo NiFi exportado (GetFile → PutMongoRecord)
├── requirements.txt    # Dependencias Python
├── models/
│   └── best.pt         # Pesos YOLOv8 entrenados (~22 MB)
└── README.md           # Este archivo
```

> **Nota:** Las imágenes se almacenan en MongoDB mediante **GridFS** (`fs.files` y `fs.chunks`), no en el sistema de ficheros local.

---

## 🧰 Stack tecnológico

| Capa | Tecnología | Uso |
|---|---|---|
| **Lenguaje** | Python 3.11 | Núcleo de toda la lógica |
| **API REST** | FastAPI + Uvicorn | Endpoint `/chat`, `/classes`, `/` |
| **Visión artificial** | YOLOv8 (Ultralytics) | Detección de ingredientes (`models/best.pt`) |
| **Dataset visión** | Roboflow — *Fridge Ingredient Detection* | Imágenes "in‑the‑wild" |
| **Base de datos** | MongoDB 7.0 + GridFS | Telemetría, recetas, imágenes |
| **Ingesta** | Apache NiFi 2.9 | GetFile + PutMongoRecord |
| **Procesamiento** | Apache Spark 4.1 (PySpark) | Medias y anomalías |
| **Orquestación IA** | n8n (LangChain Agent) | Webhook + memoria de sesión |
| **API de recetas** | Spoonacular | `recipes/findByIngredients` |
| **LLM** | OpenAI `gpt-4o-mini` (temperature 0.7) | Agente *Chef Cucharón* |
| **HTTP cliente** | httpx | Comunicación FastAPI ↔ n8n |

---

## ⚙️ Requisitos previos

Antes de empezar necesitas tener instalado:

- **Python 3.11** ([descargar](https://www.python.org/downloads/))
- **MongoDB 7.0** corriendo en `localhost:27017` ([instalar](https://www.mongodb.com/try/download/community))
- **Apache NiFi 2.9** ([descargar](https://nifi.apache.org/download.html))
- **Apache Spark 4.1** + **Java 17+** configurados en `PATH` ([Spark](https://spark.apache.org/downloads.html))
- **n8n** (cloud o self‑hosted) con un webhook activo
- Cuentas / claves API:
  - 🔑 **OpenAI API Key** (para el LLM)
  - 🔑 **Spoonacular API Key** (gratuita en [spoonacular.com](https://spoonacular.com/food-api))

> 💡 En Windows, recomendamos crear las variables de entorno `JAVA_HOME`, `SPARK_HOME`, `PYSPARK_PYTHON`, `PYSPARK_DRIVER_PYTHON`  y `HADOOP_HOME` antes de ejecutar `spark_job.py`.

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Javier-GitHU/SmartFridge.git
cd SmartFridge
```

### 2. Crear y activar un entorno virtual

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias base

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Además, necesitarás las dependencias de la API y del modelo de visión:

```bash
pip install fastapi uvicorn[standard] python-multipart httpx ultralytics pillow
```

> ⚠️ **Nota sobre PyTorch + YOLOv8 en Windows:** si la instalación de `ultralytics` no resuelve PyTorch correctamente, instálalo manualmente desde [pytorch.org](https://pytorch.org/get-started/locally/) eligiendo tu versión de CUDA (o CPU).

---

## 🛠️ Configuración

### MongoDB

Arranca MongoDB en local. El proyecto utiliza estas colecciones (se crean automáticamente al insertar el primer documento):

| Colección | Contenido |
|---|---|
| `raw_data` | Telemetría cruda de las neveras (alimentada por NiFi) |
| `processed_data` | Temperaturas medias por nevera (generadas por Spark) |
| `alerts` | Lecturas con temperatura > 10 °C |
| `recipes` | Historial completo: mensaje, ingredientes, detecciones, receta, imagen |
| `fs.files` / `fs.chunks` | Imágenes (GridFS) |

### Apache NiFi

1. Arranca NiFi (típicamente en `https://localhost:8443/nifi`).
2. En el canvas, pulsa botón derecho → **Upload template** y carga `NiFi_Flow.json`.
3. El flujo incluye:
   - **GetFile** monitoriza el directorio `/data` (ajústalo a la ruta absoluta de tu carpeta `data/`).
   - **PutMongoRecord** escribe en `smartfridge.raw_data`.
   - **MongoDBControllerService** apunta a `mongodb://host.docker.internal:27017` — cámbialo a `mongodb://localhost:27017` si NiFi no corre en Docker.
   - **JsonTreeReader** como lector de registros.
4. Habilita los *controller services* y arranca los procesadores.

### n8n

El flujo de n8n (no incluido en este repo, ver [FastAPI---SmartFridgeAI](https://github.com/alHortalV/FastAPI---SmartFridgeAI)) consta de 7 nodos:

| # | Nodo | Función |
|---|---|---|
| 1 | **Webhook** | Recibe POST con `message`, `ingredients` y `sessionId`. |
| 2 | **Extraer datos** | Normaliza el payload. |
| 3 | **Buscar en Spoonacular** | GET `findByIngredients` (`number=5`, `ranking=2`, `ignorePantry=true`). |
| 4 | **Formatear recetas** | Code node JS: prepara las recetas como bloque Markdown. |
| 5 | **AI Chef Agent** | LangChain Agent con `gpt-4o-mini` y `temperature=0.7`. |
| 6 | **Window Buffer Memory** | Memoria conversacional por `sessionId` (`contextWindowLength=10`). |
| 7 | **Respond to Webhook** | Devuelve `{ "response": "..." }` con CORS abierto. |

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `N8N_WEBHOOK_URL` | `https://iwh.persone.chat/webhook/578126b7-…` | URL del webhook de n8n |
| `MONGO_URI` | `mongodb://localhost:27017/` | URI de conexión a MongoDB *(usado directamente en código)* |

Puedes definirlas en PowerShell:

```powershell
$env:N8N_WEBHOOK_URL = "https://tu-webhook-n8n/webhook/xxx"
```

O en Linux / macOS:

```bash
export N8N_WEBHOOK_URL="https://tu-webhook-n8n/webhook/xxx"
```

---

## ▶️ Puesta en marcha

Cada componente se lanza en su propia terminal. **El orden recomendado es:**

### 1️⃣ Generador de datos IoT

```bash
python generator.py
```

Crea un fichero `../data/fridge_<timestamp>.json` con telemetría de 100 neveras cada 5 segundos.

### 2️⃣ Apache NiFi

Asegúrate de que el flujo está corriendo y consume los JSON de `/data` hacia `smartfridge.raw_data`.

### 3️⃣ Job de Spark (manual u orquestado)

```bash
python spark_job.py
```

- Lee `raw_data` de MongoDB.
- Calcula la temperatura media por `fridge_id`.
- Filtra lecturas con `temperature > 10` y las guarda en `alerts`.
- Sobrescribe `processed_data` y `alerts` (limpia antes de insertar).

### 4️⃣ API FastAPI

```bash
python FastAPI.py
# o bien
uvicorn FastAPI:app --host 0.0.0.0 --port 8000 --reload
```

La API queda accesible en **http://localhost:8000** con documentación interactiva en `/docs`.

### 5️⃣ Frontend (opcional)

Si tienes un HTML como el de [FastAPI---SmartFridgeAI](https://github.com/alHortalV/FastAPI---SmartFridgeAI), abrelo en el navegador y apunta la URL del backend a `http://localhost:8000`.

---

## 🛰️ Endpoints de la API

### `GET /`

Comprobación de salud del servicio.

```json
{
  "status": "ok",
  "service": "smart-fridge-api"
}
```

### `GET /classes`

Devuelve todas las clases de ingredientes que el modelo YOLO sabe detectar.

```json
{ "classes": ["Apple", "Banana", "Carrot", "Egg", "..."] }
```

### `POST /chat`

Endpoint principal. Acepta **dos formatos**:

#### A) `multipart/form-data` (con imagen)

| Campo | Tipo | Descripción |
|---|---|---|
| `file` | UploadFile | Imagen de la nevera |
| `message` | str | Mensaje opcional del usuario |
| `sessionId` | str | ID de sesión (mantiene contexto) |
| `ingredientsJson` | str | JSON array si ya tienes ingredientes |

#### B) `application/json` (sin imagen)

```json
{
  "message": "¿Qué puedo cocinar?",
  "ingredients": ["apple", "carrot", "egg"],
  "sessionId": "abc-123"
}
```

#### Respuesta

```json
{
  "ingredients": ["apple", "carrot", "egg"],
  "response": "## 🍽️ Tortilla de verduras\n\n**⏱️ Tiempo:** 15 min..."
}
```

Internamente, el endpoint:

1. Recibe la imagen y la guarda en GridFS.
2. Ejecuta YOLOv8 para detectar ingredientes (`confidence ≥ 0.4`).
3. Envía `message + ingredients + sessionId` al webhook de n8n.
4. Recibe la receta del *Chef Cucharón*.
5. Guarda todo (imagen, detecciones, receta, timestamp) en la colección `recipes`.

---

## 🗂️ Esquema de datos en MongoDB

### `raw_data` (alimentado por NiFi)

```json
{
  "fridge_id": 1,
  "timestamp": "2026-05-20T17:53:00",
  "temperature": 8.5,
  "door_open": true
}
```

### `processed_data` (Spark)

```json
{ "fridge_id": 1, "avg_temp": 7.83 }
```

### `alerts` (Spark)

```json
{ "fridge_id": 15, "temperature": 11.4, "door_open": true }
```

### `recipes` (FastAPI)

```json
{
  "timestamp": "2026-05-24T12:00:00",
  "sessionId": "8e1ef706-5116-4528-aa90-47ab7ae79c68",
  "user_message": "¿Qué puedo cocinar?",
  "ingredients": ["banana", "orange"],
  "detections": [
    {
      "ingredient": "banana",
      "confidence": 0.87,
      "bbox": { "x1": 120.4, "y1": 88.0, "x2": 240.1, "y2": 210.5 }
    }
  ],
  "chef_response": "## 🍽️ Macedonia tropical...",
  "image_id": "664f...",
  "filename": "nevera_alex.jpg"
}
```

---

## 🧑‍🍳 Flujo de n8n (Chef Cucharón)

El agente está configurado con un prompt sistema extenso (**v3**) cuyas reglas principales son:

- 🇪🇸 **Idioma:** responde siempre en español natural.
- 🍅 **Anti‑desperdicio:** prioriza los ingredientes perecederos.
- 🔄 **Variedad:** nunca repite recetas dentro de la misma sesión (técnica, tradición o formato distintos).
- 🔬 **Seguridad alimentaria:** avisa de mezclas peligrosas (huevo crudo, pollo poco hecho, etc.).
- 📋 **Formato fijo:** título, tiempo, dificultad, porciones, origen, ingredientes, pasos y *tip del chef*.
- 🔒 **Discreción:** nunca menciona que las recetas vienen de una API externa.

Cuando Spoonacular devuelve recetas, el chef las **traduce y adapta** al español. Si no hay candidatas adecuadas, improvisa platos coherentes con los ingredientes disponibles.

---

## 📜 Licencia

Proyecto educativo — Curso de Especialización en IA y Big Data · IES Zaidín Vergeles (Granada).
Uso libre con fines académicos y de aprendizaje.

---

<div align="center">

**Hecho con 🥄 y mucha curiosidad por**

**Alejandro Hortal Valor** · **Javier Castro Rodríguez**

*Granada · 2025/2026*

</div>
