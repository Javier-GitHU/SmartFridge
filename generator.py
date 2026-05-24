#Importamos las librerías necesarias para el generador de datos. 
# json para manejar archivos JSON, random para generar valores aleatorios, 
# time para manejar el tiempo, datetime para obtener la fecha y hora actual, 
# y os para manejar el sistema de archivos.
import json
import random
import time
from datetime import datetime
import os
#Creamos un directorio llamado "data" en el nivel superior del proyecto para almacenar los archivos JSON generados.
os.makedirs("../data", exist_ok=True)
#Creamos la funcion para generar los datos de las neveras inteligentes. 
# Esta función toma un parámetro fridge_id y devuelve un diccionario con la información de la nevera
# incluyendo el ID, la marca de tiempo, la temperatura y si la puerta está abierta o cerrada.
def generar_dato(fridge_id):
#Devolvemos aquí un diccionario con los datos generados para la nevera inteligente.
    return {
        # ID de la nevera
        "fridge_id": fridge_id,
        # Marca de tiempo actual en formato ISO 8601
        "timestamp": datetime.now().isoformat(),
        # Temperatura en grados Celsius, redondeada a 2 decimales y generada aleatoriamente entre 2 y 12 grados
        "temperature": round(random.uniform(2, 12), 2),
        # Estado de la puerta (True si está abierta, False si está cerrada) generado aleatoriamente
        "door_open": random.choice([True, False])
    }
#El siguiente bloque de codigo es un bucle infinito que genera datos para 100 neveras inteligentes cada 5 segundos.
while True:
#Creamos una lista vacía para almacenar los datos generados.
    datos = []
#Generamos datos para 100 neveras inteligentes utilizando un bucle for.
    for i in range(100):
#Llamamos a la función generar_dato para cada nevera, pasando el ID de la nevera (i) como argumento segun en cual parte del bucle estemos sera un id
#y agregamos el resultado a la lista de datos.
        datos.append(
            generar_dato(i)
        )
#Generamos un nombre de archivo único para cada conjunto de datos utilizando la marca de tiempo actual.
    filename = f"../data/fridge_{int(time.time())}.json"
#Guardamos los datos generados en un archivo JSON utilizando la función json.dump.
    with open(filename, "w") as f:

        json.dump(datos, f, indent=2)
#Imprimimos un mensaje en la consola indicando que el archivo ha sido generado.
    print(f"{filename} generado")
#Esperamos 5 segundos antes de generar el siguiente conjunto de datos para evitar generar archivos demasiado rápido.
    time.sleep(5)