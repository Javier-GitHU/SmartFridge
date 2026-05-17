from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
from pymongo import MongoClient
from datetime import datetime
import io
import os

# =========================
# FASTAPI
# =========================

app = FastAPI(
    title="Smart Fridge AI",
    description="API que detecta ingredientes en fotos de neveras",
    version="0.1.0"
)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MONGODB
# =========================

client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# =========================
# CARPETA IMÁGENES
os.makedirs("images", exist_ok=True)

# =========================
# MODELO YOLO
# =========================

print("⏳ Cargando modelo YOLOv8...")
model = YOLO("models/best.pt")
print(f"✅ Modelo cargado. Clases disponibles: {len(model.names)}")

# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "smart-fridge-api",
        "num_classes": len(model.names)
    }

# =========================
# CLASES
# =========================

@app.get("/classes")
def list_classes():
    return {"classes": list(model.names.values())}

# =========================
# DETECCIÓN
# =========================

@app.post("/detect")
async def detect_ingredients(
    file: UploadFile = File(...),
    confidence: float = 0.4
):

    # Validar imagen
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )

    # Leer imagen
    contents = await file.read()

    # Guardar imagen
    image_path = f"images/{datetime.now().timestamp()}_{file.filename}"

    with open(image_path, "wb") as f:
        f.write(contents)

    # Abrir imagen
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Imagen inválida")

    # Predicción YOLO
    results = model.predict(image, conf=confidence, verbose=False)

    # Procesar detecciones
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

    # Ingredientes únicos
    unique_ingredients = sorted(
        set(d["ingredient"] for d in detections)
    )

    # =========================
    # GUARDAR EN MONGODB
    # =========================

    prediction_data = {
        "timestamp": datetime.now().isoformat(),
        "image_path": image_path,
        "ingredients": unique_ingredients,
        "detections": detections,
        "total_detections": len(detections),
        "image_size": {
            "width": image.width,
            "height": image.height
        }
    }

    print("Intentando guardar en Mongo...")
    db.predictions.insert_one(prediction_data)
    print("Guardado correctamente") 
    # =========================
    # RESPUESTA
    # =========================

    return {
        "ingredients": unique_ingredients,
        "detections": detections,
        "total_detections": len(detections),
        "image_size": {
            "width": image.width,
            "height": image.height
        }
    }

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)