from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
from typing import Optional
from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime

import io
import os
import json
import httpx

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://iwh.persone.chat/webhook/578126b7-c4de-4b6b-8151-d6d6549df198"
)

# ─────────────────────────────────────────────────────────────
# MONGODB
# ─────────────────────────────────────────────────────────────

client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# GridFS
fs = GridFS(db)

# ─────────────────────────────────────────────────────────────
# FASTAPI
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Fridge AI",
    description="API IA neveras inteligentes",
    version="1.0.0"
)

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# YOLO
# ─────────────────────────────────────────────────────────────

print("⏳ Cargando YOLO...")

model = YOLO("models/best.pt")

print("✅ YOLO cargado")

# ─────────────────────────────────────────────────────────────
# DETECCIÓN
# ─────────────────────────────────────────────────────────────

def detect_from_image(image: Image.Image, confidence: float = 0.4):

    results = model.predict(
        image,
        conf=confidence,
        verbose=False
    )

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
        "service": "smart-fridge-api"
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
# CHAT
# ─────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(
    message: str = Form(""),
    sessionId: str = Form("default"),
    ingredientsJson: str = Form("[]"),
    file: Optional[UploadFile] = File(None)
):

    timestamp = datetime.now().isoformat()

    image_id = None
    filename = None
    detections = []

    # ─────────────────────────────────────────
    # FOTO
    # ─────────────────────────────────────────

    if file:

        if (
            file.content_type and
            not file.content_type.startswith("image/")
        ):

            raise HTTPException(
                status_code=400,
                detail="Debe ser una imagen"
            )

        contents = await file.read()

        # Guardar imagen en Mongo
        image_id = fs.put(
            contents,
            filename=file.filename,
            content_type=file.content_type
        )

        filename = file.filename

        try:

            image = Image.open(
                io.BytesIO(contents)
            ).convert("RGB")

        except Exception:

            raise HTTPException(
                status_code=400,
                detail="Imagen inválida"
            )

        detections, ingredients = detect_from_image(image)

    else:

        # Ingredientes ya existentes

        try:

            ingredients = json.loads(
                ingredientsJson
            ) if ingredientsJson else []

            if not isinstance(ingredients, list):
                ingredients = []

        except json.JSONDecodeError:

            ingredients = []

    # ─────────────────────────────────────────
    # N8N
    # ─────────────────────────────────────────

    payload = {
        "message": message or "¿Qué puedo cocinar con esto?",
        "ingredients": ingredients,
        "sessionId": sessionId
    }

    try:

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload
            )

            response.raise_for_status()

            n8n_data = response.json()

    except httpx.TimeoutException:

        raise HTTPException(
            status_code=504,
            detail="Timeout chef IA"
        )

    except httpx.HTTPError as e:

        raise HTTPException(
            status_code=502,
            detail=f"Error n8n: {str(e)}"
        )

    chef_response = n8n_data.get("response", "")

    # ─────────────────────────────────────────
    # GUARDAR TODO EN MONGO
    # ─────────────────────────────────────────

    recipe_data = {
        "timestamp": timestamp,
        "sessionId": sessionId,
        "user_message": message,
        "ingredients": ingredients,
        "detections": detections,
        "chef_response": chef_response
    }

    if image_id:

        recipe_data["image_id"] = str(image_id)
        recipe_data["filename"] = filename

    db.recipes.insert_one(recipe_data)

    # ─────────────────────────────────────────
    # RESPUESTA
    # ─────────────────────────────────────────

    return {
        "ingredients": ingredients,
        "response": chef_response
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