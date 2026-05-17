import json
import random
import time
from datetime import datetime

def generar_dato(fridge_id):
    return {
        "fridge_id": fridge_id,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(2, 12), 2),
        "door_open": random.choice([True, False])
    }

while True:

    datos = []

    for i in range(100):
        datos.append(generar_dato(i))

    filename = f"data/fridge_{int(time.time())}.json"

    with open(filename, "w") as f:
        json.dump(datos, f, indent=2)

    print(f"{filename} generado")

    time.sleep(5)