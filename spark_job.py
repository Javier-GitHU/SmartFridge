from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col
from pymongo import MongoClient
import os
import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
# =========================
# MONGODB
# =========================

client = MongoClient("mongodb://localhost:27017/")

db = client["smartfridge"]

# Leer datos
data = list(db.raw_data.find())

# =========================
# ELIMINAR _id
# =========================

for doc in data:

    doc.pop("_id", None)

# =========================
# SPARK
# =========================

spark = SparkSession.builder \
    .appName("SmartFridge") \
    .getOrCreate()

df = spark.createDataFrame(data)

# =========================
# MEDIA TEMPERATURA
# =========================

avg_df = df.groupBy("fridge_id").agg(
    avg("temperature").alias("avg_temp")
)

print("\n=== TEMPERATURAS MEDIAS ===")

avg_df.show()

# =========================
# ALERTAS
# =========================

alerts_df = df.filter(
    col("temperature") > 10
)
print("\n=== ALERTAS TEMPERATURA ===")
alerts_df.show()