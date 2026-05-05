from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from pymongo import MongoClient

# Conexión Mongo
client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# Leer datos
data = list(db.raw_data.find())

# Crear Spark
spark = SparkSession.builder.appName("SmartFridge").getOrCreate()

df = spark.createDataFrame(data)

# 📊 Media temperatura
avg_df = df.groupBy("fridge_id").agg(avg("temperature").alias("avg_temp"))

# 🚨 Detectar anomalías
alerts_df = df.filter(col("temperature") > 10)

# Convertir resultados
avg_list = avg_df.toPandas().to_dict("records")
alerts_list = alerts_df.toPandas().to_dict("records")

# Guardar resultados
db.processed_data.delete_many({})
if avg_list:
    db.processed_data.insert_many(avg_list)

if alerts_list:
    db.alerts.insert_many(alerts_list)

print("Procesamiento terminado")