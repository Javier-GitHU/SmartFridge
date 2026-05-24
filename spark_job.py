# Este script es un trabajo de Spark que se conecta a MongoDB, lee los datos de las neveras inteligentes, 
# calcula la temperatura media por nevera, identifica las alertas de temperatura y guarda los resultados procesados de nuevo en MongoDB.
# Importamos las librerías necesarias para el trabajo de Spark y MongoDB.
# pyspark.sql para trabajar con Spark, pymongo para conectarnos a MongoDB, os y sys para manejar variables de entorno y el sistema de archivos.
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col
from pymongo import MongoClient
import os
import sys


# PYSPARK
# Configuramos las variables de entorno para que PySpark use el mismo intérprete de Python que el script actual.
# Esto es importante para asegurar que las dependencias de Python se manejen correctamente tanto en el driver como en los workers de Spark.
#Y por eso es necesario configurar estas variables de entorno para evitar problemas de compatibilidad entre el entorno de Python del script 
# y el entorno de Python que Spark utiliza para ejecutar las tareas distribuidas.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


# MONGODB
# Configuramos la conexión a MongoDB utilizando pymongo. Nos conectamos a la base de datos "smartfridge" y accedemos a las colecciones necesarias que 
# este caso es "raw_data" para leer los datos de las neveras sin procesar.
client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# Leemos los datos de la colección "raw_data" y los convertimos a una lista de diccionarios para poder procesarlos con Spark.
data = list(db.raw_data.find())

# ELIMINAR _id
# MongoDB agrega automáticamente un campo "_id" a cada documento pero este campo no es necesario para nuestro análisis 
# y puede causar problemas al convertir los datos a un DataFrame de Spark por lo que lo borramos
for doc in data:
    doc.pop("_id", None)


# SPARK
# Creamos una sesión de Spark llamada "SmartFridge" y 
# convertimos la lista de diccionarios a un DataFrame de Spark para poder realizar las operaciones de análisis.
spark = SparkSession.builder \
    .appName("SmartFridge") \
    .getOrCreate()

df = spark.createDataFrame(data)


# TEMPERATURA MEDIA
# Calculamos la temperatura media por nevera utilizando la función avg de Spark y agrupando por el campo "fridge_id" con groupby
avg_df = df.groupBy("fridge_id").agg(
    avg("temperature").alias("avg_temp")
)
# Mostramos las temperaturas medias por nevera en la consola utilizando el método show de Spark.
print("\n=== TEMPERATURAS MEDIAS ===")
avg_df.show()


# ALERTAS
# Identificamos las alertas de temperatura filtrando el DataFrame original para encontrar las filas donde 
# la temperatura es mayor a 10 grados utilizando el método filter de Spark.
alerts_df = df.filter(
    col("temperature") > 10
)
#Y las mostramos
print("\n=== ALERTAS TEMPERATURA ===")
alerts_df.show()


# GUARDAR ALERTAS EN MONGO
# Convertimos los DataFrames de Spark a listas de diccionarios para poder guardarlos en MongoDB utilizando pymongo.
alerts_list = alerts_df.toPandas().to_dict("records")
# Antes de insertar las nuevas alertas, eliminamos las alertas anteriores de la colección "alerts" para evitar duplicados y mantener la colección limpia.
db.alerts.delete_many({})

if alerts_list:
# Insertamos las nuevas alertas en la colección "alerts" de MongoDB utilizando el método insert_many de pymongo.
    db.alerts.insert_many(alerts_list)
# Imprimimos un mensaje en la consola indicando cuántas alertas se han guardado en MongoDB.
    print(f"\n✅ {len(alerts_list)} alertas guardadas en MongoDB")


# GUARDAR MEDIAS EN MONGO
# De manera similar a las alertas, convertimos el DataFrame de temperaturas medias a una lista de diccionarios 
# y guardamos los resultados en la colección "processed_data" de MongoDB.
avg_list = avg_df.toPandas().to_dict("records")
# Antes de insertar las nuevas medias, eliminamos las medias anteriores de la colección "processed_data" para evitar duplicados 
# y mantener la colección limpia como en el anterior
db.processed_data.delete_many({})
# Insertamos las nuevas medias en la colección "processed_data" de MongoDB utilizando el método insert_many de pymongo.
if avg_list:
    db.processed_data.insert_many(avg_list)
# Imprimimos un mensaje en la consola indicando cuántas medias se han guardado en MongoDB.
    print(f"\n✅ {len(avg_list)} medias guardadas en MongoDB")