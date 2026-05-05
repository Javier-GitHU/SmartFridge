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
    with open("fridge_data.json", "w") as f:
        for i in range(100):
            f.write(json.dumps(generar_dato(i)) + "\n")

    print("Datos generados...")
    time.sleep(5)