from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
from typing import Optional
from pymongo import MongoClient
from datetime import datetime

import io
import os
import json
import httpx

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://iwh.persone.chat/webhook/578126b7-c4de-4b6b-8151-d6d6549df198"
)

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# Carpeta imágenes
os.makedirs("images", exist_ok=True)

# Crear app
app = FastAPI(
    title="Smart Fridge AI",
    description="API que detecta ingredientes en fotos de neveras y orquesta el chat con el chef",
    version="0.3.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# CARGAR YOLO
# ─────────────────────────────────────────────────────────────

print("⏳ Cargando modelo YOLOv8...")

model = YOLO("models/best.pt")

print(f"✅ Modelo cargado. Clases disponibles: {len(model.names)}")
print(f"🔗 Webhook de n8n configurado en: {N8N_WEBHOOK_URL}")

# ─────────────────────────────────────────────────────────────
# DETECCIÓN YOLO
# ─────────────────────────────────────────────────────────────

def detect_from_image(image: Image.Image, confidence: float = 0.4):

    results = model.predict(image, conf=confidence, verbose=False)

    detections = []

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            conf_score = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "ingredient": class_name,
                "confidence": round(conf_score, 3),
                "bbox": {
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "x2": round(x2, 1),
                    "y2": round(y2, 1),
                }
            })

    unique_ingredients = sorted(
        set(d["ingredient"] for d in detections)
    )

    return detections, unique_ingredients

# ─────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():

    return {
        "status": "ok",
        "service": "smart-fridge-api",
        "num_classes": len(model.names),
        "n8n_webhook": N8N_WEBHOOK_URL
    }

# ─────────────────────────────────────────────────────────────
# CLASES
# ─────────────────────────────────────────────────────────────

@app.get("/classes")
def list_classes():

    return {
        "classes": list(model.names.values())
    }

# ─────────────────────────────────────────────────────────────
# DETECT
# ─────────────────────────────────────────────────────────────

@app.post("/detect")
async def detect_ingredients(
    file: UploadFile = File(...),
    confidence: float = 0.4
):

    if not file.content_type or not file.content_type.startswith("image/"):

        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    contents = await file.read()

    # Timestamp del request
    message_timestamp = datetime.now().isoformat()

    # Guardar imagen
    image_path = f"images/{datetime.now().timestamp()}_{file.filename}"

    with open(image_path, "wb") as f:
        f.write(contents)

    try:

        image = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Imagen inválida o corrupta"
        )

    detections, ingredients = detect_from_image(
        image,
        confidence
    )

    # ─────────────────────────────────────────
    # GUARDAR EN MONGO
    # ─────────────────────────────────────────

    prediction_data = {
        "timestamp": message_timestamp,
        "image_path": image_path,
        "ingredients": ingredients,
        "detections": detections,
        "total_detections": len(detections),
        "image_size": {
            "width": image.width,
            "height": image.height
        }
    }

    db.predictions.insert_one(prediction_data)

    return {
        "ingredients": ingredients,
        "detections": detections,
        "total_detections": len(detections),
        "image_size": {
            "width": image.width,
            "height": image.height
        },
        "messageTimestamp": message_timestamp
    }

# ─────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(
    message: str = Form(""),
    sessionId: str = Form("default"),
    ingredientsJson: str = Form("[]"),
    file: Optional[UploadFile] = File(None)
):

    # ─────────────────────────────────────────
    # TIMESTAMP DEL MENSAJE
    # ─────────────────────────────────────────

    message_timestamp = datetime.now().isoformat()

    # ─────────────────────────────────────────
    # OBTENER INGREDIENTES
    # ─────────────────────────────────────────

    if file:

        if file.content_type and not file.content_type.startswith("image/"):

            raise HTTPException(
                status_code=400,
                detail="El archivo debe ser una imagen"
            )

        contents = await file.read()

        # Guardar imagen
        image_path = f"images/{datetime.now().timestamp()}_{file.filename}"

        with open(image_path, "wb") as f:
            f.write(contents)

        try:

            image = Image.open(
                io.BytesIO(contents)
            ).convert("RGB")

        except Exception:

            raise HTTPException(
                status_code=400,
                detail="Imagen inválida o corrupta"
            )

        detections, ingredients = detect_from_image(
            image,
            confidence=0.4
        )

        # Guardar en Mongo
        prediction_data = {
            "timestamp": message_timestamp,
            "image_path": image_path,
            "ingredients": ingredients,
            "detections": detections,
            "total_detections": len(detections),
            "sessionId": sessionId
        }

        db.predictions.insert_one(prediction_data)

    else:

        try:

            ingredients = json.loads(
                ingredientsJson
            ) if ingredientsJson else []

            if not isinstance(ingredients, list):
                ingredients = []

        except json.JSONDecodeError:

            ingredients = []

    # ─────────────────────────────────────────
    # LLAMAR N8N
    # ─────────────────────────────────────────

    payload = {
        "message": message or "¿Qué puedo cocinar con esto?",
        "ingredients": ingredients,
        "sessionId": sessionId,
        "messageTimestamp": message_timestamp
    }

    try:

        async with httpx.AsyncClient(timeout=60.0) as client:

            n8n_res = await client.post(
                N8N_WEBHOOK_URL,
                json=payload
            )

            n8n_res.raise_for_status()

            n8n_data = n8n_res.json()

    except httpx.TimeoutException:

        raise HTTPException(
            status_code=504,
            detail="El chef está tardando demasiado en responder."
        )

    except httpx.HTTPError as e:

        raise HTTPException(
            status_code=502,
            detail=f"Error llamando a n8n: {str(e)}"
        )

    # ─────────────────────────────────────────
    # RESPUESTA FINAL
    # ─────────────────────────────────────────

    return {
        "ingredients": ingredients,
        "response": n8n_data.get("response", ""),
        "messageTimestamp": message_timestamp
    }

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )