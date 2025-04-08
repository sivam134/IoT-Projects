# smart_home_controller_simple.py

import time, json, sqlite3, random
from datetime import datetime
import paho.mqtt.client as mqtt

# Config
DB = "smart_home.db"
BROKER = "localhost"
PORT = 1883
TEMP_LIMIT = 28.0
INTERVAL = 10
TOPIC_TEMP = "home/sensors/temperature"
TOPIC_ALERT = "home/alerts"

# Simulated sensor
def read_temp(): return 22 + random.uniform(-2, 6)
def read_humid(): return 50 + random.uniform(-10, 20)

# Create tables
def setup_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS readings (
                        id INTEGER PRIMARY KEY, time TEXT, temp REAL, humid REAL, alert INTEGER)''')
        con.commit()

# Store reading
def save_reading(temp, humid, alert):
    with sqlite3.connect(DB) as con:
        con.execute("INSERT INTO readings (time, temp, humid, alert) VALUES (?, ?, ?, ?)",
                    (datetime.now().isoformat(), temp, humid, alert))
        con.commit()

# MQTT Setup
client = mqtt.Client()

def connect_mqtt():
    client.connect(BROKER, PORT)
    client.loop_start()

def publish(topic, payload):
    client.publish(topic, json.dumps(payload))

# Alert function
def send_alert(temp, humid):
    print(f"🚨 ALERT: Temp {temp:.1f}°C exceeds {TEMP_LIMIT}°C")
    publish(TOPIC_ALERT, {
        "type": "high_temp",
        "temp": temp,
        "humid": humid,
        "time": datetime.now().isoformat()
    })

# Main loop
def main():
    setup_db()
    connect_mqtt()

    while True:
        temp = read_temp()
        humid = read_humid()
        alert = int(temp > TEMP_LIMIT)

        save_reading(temp, humid, alert)
        publish(TOPIC_TEMP, {"temp": temp, "humid": humid, "time": datetime.now().isoformat()})

        if alert:
            send_alert(temp, humid)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        client.loop_stop()
        print("\nSmart Home Controller stopped.")

