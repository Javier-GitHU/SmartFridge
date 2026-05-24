
# Este código implementa una API REST utilizando FastAPI para manejar las interacciones con la nevera inteligente. 
# La API permite a los usuarios enviar mensajes, subir imágenes de los ingredientes en la nevera, 
# y recibir respuestas generadas por una IA chef a través de un flujo de trabajo en n8n. 
# Además, la API guarda toda la información relevante en MongoDB para su posterior análisis y referencia.
# La API también utiliza un modelo de detección de objetos basado en YOLO para identificar 
# los ingredientes presentes en las imágenes subidas por los usuarios.
# Importamos las librerías necesarias para la API. FastAPI para crear la API, File y UploadFile 
# para manejar la subida de archivos, HTTPException para manejar errores, Form para manejar datos de formulario,
# CORSMiddleware para manejar CORS, YOLO para la detección de objetos, PIL para manejar imágenes,
# typing para manejar tipos de datos opcionales, pymongo para conectarnos a MongoDB, gridfs para manejar archivos grandes en MongoDB,
# datetime para manejar fechas y horas, io para manejar flujos de datos en memoria, os para manejar el sistema de archivos,
# json para manejar datos en formato JSON, y httpx para hacer solicitudes HTTP asíncronas.
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


# CONFIG
# Configuramos la URL del webhook de n8n utilizando una variable de entorno para que pueda ser fácilmente cambiada sin modificar el código. 
# Si la variable de entorno no está configurada, se utiliza una URL de webhook de n8n
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "https://iwh.persone.chat/webhook/578126b7-c4de-4b6b-8151-d6d6549df198"
)


# MONGODB
# Configuramos la conexión a MongoDB utilizando pymongo. Nos conectamos a la base de datos "smartfridge" 
# y accedemos a las colecciones necesarias que en este caso es "recipes" para guardar las interacciones con la IA chef 
client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# GridFS es una especificación para almacenar y recuperar archivos que superan el límite de tamaño de documentos de MongoDB (16 MB). 
# GridFS divide un archivo en partes más pequeñas, las almacena como documentos separados y luego 
# las vuelve a ensamblar cuando se recupera el archivo. En este caso, lo usamos para almacenar las imágenes subidas por los usuarios.
fs = GridFS(db)

# Creamos la instancia de FastAPI para definir nuestra API REST. Configuramos el título, la descripción y 
# la versión de la API para que sea más fácil de entender y usar por los desarrolladores que interactúen con ella.
app = FastAPI(
    # Título de la API
    title="Smart Fridge AI",
    # Descripción de la API
    description="API IA neveras inteligentes",
    # Versión de la API
    version="1.0.0"
)


# CORS
# Configuramos CORS (Cross-Origin Resource Sharing) para permitir que la API sea accedida desde cualquier origen,
# lo que es útil durante el desarrollo y para permitir que cualquier cliente pueda interactuar con la API sin restricciones de origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# YOLO
# Cargamos el modelo de detección de objetos YOLO desde el archivo "models/best.pt". 
# Este modelo ha sido entrenado para detectar los ingredientes presentes en la nevera inteligente.
print("⏳ Cargando YOLO...")

model = YOLO("models/best.pt")

print("✅ YOLO cargado")

# DETECCIÓN
# Definimos una función detect_from_image que toma una imagen y un umbral de confianza como parámetros,
# y devuelve una lista de detecciones y una lista de ingredientes únicos detectados en la imagen
# La función utiliza el modelo YOLO para predecir los objetos presentes en la imagen, 
# y luego procesa los resultados para extraer la información relevante de cada detección, 
# como el nombre del ingrediente, la confianza de la detección y las coordenadas del cuadro delimitador (bounding box).
def detect_from_image(image: Image.Image, confidence: float = 0.4):
# Utilizamos el modelo YOLO para predecir los objetos presentes en la imagen, pasando la imagen y el umbral de confianza como parámetros. 
# El modelo devuelve una lista de resultados que contienen las detecciones realizadas en la imagen.
    results = model.predict(
        image,
        conf=confidence,
        verbose=False
    )
# Creamos una lista vacía para almacenar las detecciones procesadas.
    detections = []
# Procesamos los resultados de las detecciones para extraer la información relevante de cada detección,
# como el nombre del ingrediente, la confianza de la detección y las coordenadas del cuadro delimitador (bounding box).
    for result in results:
        for box in result.boxes:
            # Extraemos el ID de la clase detectada, el nombre de la clase utilizando el modelo, 
            # la confianza de la detección y las coordenadas del cuadro delimitador.
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            conf_score = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            # Agregamos la detección a la lista de detecciones con la información extraída.
            # Cada detección es un diccionario que contiene el nombre del ingrediente, 
            # la confianza de la detección y las coordenadas del cuadro delimitador.
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
# Creamos una lista de ingredientes únicos detectados en la imagen utilizando un conjunto (set) 
# para eliminar duplicados y luego ordenamos la lista alfabéticamente.
    unique_ingredients = sorted(
        set(d["ingredient"] for d in detections)
    )
# Devolvemos la lista de detecciones y la lista de ingredientes únicos detectados en la imagen.
    return detections, unique_ingredients


# ROOT
# Definimos un endpoint raíz ("/") que devuelve un mensaje de estado para indicar que la API está funcionando correctamente.
# Este endpoint es útil para verificar rápidamente que la API está en línea y respondiendo a las solicitudes.
@app.get("/")
def root():
# Devolvemos un diccionario con el estado de la API y el nombre del servicio para indicar que la API está funcionando correctamente.
    return {
        "status": "ok",
        "service": "smart-fridge-api"
    }


# CLASES
# Definimos un endpoint "/classes" que devuelve la lista de clases que el modelo YOLO puede detectar.
# Este endpoint es útil para que los desarrolladores que interactúan con la API puedan conocer
#  qué ingredientes pueden ser detectados por el modelo y utilizarlos en sus solicitudes.
@app.get("/classes")
def list_classes():
# Devolvemos un diccionario con la lista de clases que el modelo YOLO puede detectar, 
# utilizando el atributo "names" del modelo para obtener los nombres de las clases.
    return {
        "classes": list(model.names.values())
    }


# CHAT
# Definimos un endpoint "/chat" que maneja las interacciones con la IA chef. Este endpoint acepta un mensaje del usuario,
# un ID de sesión para agrupar las interacciones, una lista de ingredientes en formato JSON, 
# y una imagen opcional de los ingredientes en la nevera.
@app.post("/chat")
async def chat(
    message: str = Form(""),
    sessionId: str = Form("default"),
    ingredientsJson: str = Form("[]"),
    file: Optional[UploadFile] = File(None)
):
# Obtenemos la marca de tiempo actual en formato ISO 8601 para registrar cuándo se realizó la interacción con la IA chef.
    timestamp = datetime.now().isoformat()
# Inicializamos variables para almacenar el ID de la imagen, el nombre del archivo y las detecciones realizadas en la imagen.
    image_id = None
    filename = None
    detections = []


    # FOTO
    # Si se ha subido un archivo, procesamos la imagen para detectar los ingredientes presentes en ella.
    if file:
        # Validamos que el archivo subido sea una imagen verificando su tipo de contenido (content_type). 
        # Si el archivo no es una imagen, lanzamos una excepción HTTP con un código de estado 400
        if (
            file.content_type and
            not file.content_type.startswith("image/")
        ):
        # Si el archivo no es una imagen, lanzamos una excepción HTTP con un código de estado 400 
        # y un mensaje de error indicando que debe ser una imagen.
            raise HTTPException(
                status_code=400,
                detail="Debe ser una imagen"
            )
        # Leemos el contenido del archivo subido utilizando el método read de UploadFile,
        # que devuelve los datos del archivo en formato binario.
        contents = await file.read()

        # Guardamos la imagen en GridFS de MongoDB utilizando el método put de GridFS, que devuelve un ID único para la imagen almacenada.
        image_id = fs.put(
            contents,
            filename=file.filename,
            content_type=file.content_type
        )
        # Guardamos el nombre del archivo para referencia futura, aunque la imagen se almacena en GridFS utilizando el ID generado.
        filename = file.filename
        # Procesamos la imagen para detectar los ingredientes presentes en ella utilizando la función detect_from_image definida anteriormente. 
        # Si la detección es exitosa, obtenemos las detecciones y la lista de
        # ingredientes únicos detectados en la imagen. 
        # Si la imagen no es válida o no se puede procesar, lanzamos una excepción HTTP 
        # con un código de estado 400 y un mensaje de error indicando que la imagen es inválida.
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
    # Si no se ha subido una imagen, intentamos obtener la lista de ingredientes a partir del campo ingredientsJson enviado en el formulario.
    else:

        # Intentamos cargar la lista de ingredientes desde el campo ingredientsJson,
        # que se espera que sea una cadena JSON que representa una lista de ingredientes.
        # Si el campo ingredientsJson está vacío o no es una lista válida, 
        # se asigna una lista vacía a la variable ingredients. Si el campo ingredientsJson no es un JSON válido, 
        # se captura la excepción JSONDecodeError y también se asigna una lista vacía a ingredients.
        try:

            ingredients = json.loads(
                ingredientsJson
            ) if ingredientsJson else []

            if not isinstance(ingredients, list):
                ingredients = []

        except json.JSONDecodeError:

            ingredients = []

    # N8N
    # Preparamos el payload para enviar a n8n, que incluye el mensaje del usuario, la lista de ingredientes y el ID de sesión. 
    # Este payload se enviará al webhook de n8n para que la IA chef pueda procesar la información
    # y generar una respuesta basada en los ingredientes disponibles y el mensaje del usuario.
    payload = {
        "message": message or "¿Qué puedo cocinar con esto?",
        "ingredients": ingredients,
        "sessionId": sessionId
    }
    # Si se ha subido una imagen, también incluimos el ID de la imagen en el payload para que n8n pueda acceder a ella si es necesario 
    # para generar la respuesta de la IA chef.
    try:

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload
            )
            response.raise_for_status()
            n8n_data = response.json()
# Manejamos posibles excepciones que pueden ocurrir durante la solicitud HTTP a n8n, como timeouts o errores de conexión.
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
# Obtenemos la respuesta generada por la IA chef desde los datos devueltos por n8n. 
# La respuesta se espera que esté en el campo "response" del JSON devuelto por n8n
    chef_response = n8n_data.get("response", "")


    # GUARDAR TODO EN MONGO
    # Preparamos un diccionario con toda la información relevante de la interacción para guardarla en MongoDB.
    recipe_data = {
        #Timestamp de la interacción
        "timestamp": timestamp,
        # ID de sesión para agrupar las interacciones relacionadas
        "sessionId": sessionId,
        # Mensaje del usuario enviado a la IA chef
        "user_message": message,
        # Lista de ingredientes detectados o enviados por el usuario
        "ingredients": ingredients,
        # Lista de detecciones realizadas en la imagen, si se subió una imagen
        "detections": detections,
        # Respuesta generada por la IA chef basada en el mensaje y los ingredientes
        "chef_response": chef_response
    }
# Si se ha subido una imagen, también incluimos el ID de la imagen y el nombre del archivo en el diccionario 
# que se guardará en MongoDB para referencia futura.
    if image_id:
        recipe_data["image_id"] = str(image_id)
        recipe_data["filename"] = filename

    db.recipes.insert_one(recipe_data)

    # RESPUESTA
    # Devolvemos un diccionario con la lista de ingredientes detectados o enviados por el usuario y la respuesta generada por la IA chef.
    return {
        "ingredients": ingredients,
        "response": chef_response
    }


# MAIN
# Ejecutamos la aplicación FastAPI utilizando Uvicorn como servidor ASGI. La aplicación se ejecutará en el host "0.0.0.0" 
# para que sea accesible desde cualquier dirección IP, y en el puerto 8000.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )