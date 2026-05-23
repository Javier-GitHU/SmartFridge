from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col
from pymongo import MongoClient
import os
import sys

# =========================
# PYSPARK
# =========================

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# =========================
# MONGODB
# =========================

client = MongoClient("mongodb://localhost:27017/")
db = client["smartfridge"]

# Leer datos IoT
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
# TEMPERATURA MEDIA
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

# =========================
# GUARDAR ALERTAS EN MONGO
# =========================

alerts_list = alerts_df.toPandas().to_dict("records")

db.alerts.delete_many({})

if alerts_list:

    db.alerts.insert_many(alerts_list)

    print(f"\n✅ {len(alerts_list)} alertas guardadas en MongoDB")

# =========================
# GUARDAR MEDIAS EN MONGO
# =========================

avg_list = avg_df.toPandas().to_dict("records")

db.processed_data.delete_many({})

if avg_list:

    db.processed_data.insert_many(avg_list)

    print(f"\n✅ {len(avg_list)} medias guardadas en MongoDB")