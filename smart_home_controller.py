# smart_home_controller.py

import time
import json
import sqlite3
import os
from datetime import datetime
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import random  # For simulating sensor data
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("smart_home.log"), logging.StreamHandler()]
)
logger = logging.getLogger("SmartHome")

# Configuration
DB_PATH = "smart_home.db"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TEMP_THRESHOLD = 28.0
CHECK_INTERVAL = 10  # seconds

# Define MQTT topics
TOPIC_TEMP = "home/sensors/temperature"
TOPIC_LIGHTS = "home/devices/lights"
TOPIC_THERMOSTAT = "home/devices/thermostat"
TOPIC_LOCK = "home/devices/lock"

class SmartHomeSensor:
    """Simulates temperature and humidity sensor readings"""
    
    def read_temperature(self):
        # Simulate temperature reading (normally between 20-25°C)
        return 22.0 + random.uniform(-2, 6)  
        
    def read_humidity(self):
        # Simulate humidity reading (normally between 40-60%)
        return 50.0 + random.uniform(-10, 20)

class Database:
    """Handles database operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Create the database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for sensor readings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            alert_triggered INTEGER
        )
        ''')
        
        # Create table for device states
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE,
            device_type TEXT,
            state TEXT,
            last_updated TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
        
    def store_reading(self, temperature, humidity, alert_triggered=0):
        """Store sensor reading in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO sensor_readings (timestamp, temperature, humidity, alert_triggered) VALUES (?, ?, ?, ?)",
            (timestamp, temperature, humidity, alert_triggered)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Stored reading: temp={temperature:.1f}°C, humidity={humidity:.1f}%")
        
    def update_device_state(self, device_id, device_type, state):
        """Update device state in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO device_states (device_id, device_type, state, last_updated) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(device_id) 
            DO UPDATE SET state = ?, last_updated = ?
            """,
            (device_id, device_type, state, timestamp, state, timestamp)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Updated device state: {device_id} ({device_type}) = {state}")
        
    def get_device_state(self, device_id):
        """Get current state of a device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT state FROM device_states WHERE device_id = ?",
            (device_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
        
    def get_recent_readings(self, limit=10):
        """Get recent sensor readings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp, temperature, humidity FROM sensor_readings ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        return results

class MQTTController:
    """Handles MQTT communications"""
    
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.database = Database(DB_PATH)
        
    def connect(self):
        """Connect to the MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        logger.info(f"MQTT connection established with result code {rc}")
        # Subscribe to all device control topics
        client.subscribe(TOPIC_LIGHTS + "/#")
        client.subscribe(TOPIC_THERMOSTAT + "/#")
        client.subscribe(TOPIC_LOCK + "/#")
        
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            logger.info(f"Message received on {msg.topic}: {msg.payload.decode()}")
            payload = json.loads(msg.payload.decode())
            
            # Extract device info from topic
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                device_type = topic_parts[2]  # e.g., "lights", "thermostat", "lock"
                device_id = topic_parts[3] if len(topic_parts) > 3 else "default"
                
                # Store device state in database
                if 'state' in payload:
                    self.database.update_device_state(device_id, device_type, payload['state'])
                    
                    # Handle device-specific logic
                    if device_type == "thermostat" and 'temperature' in payload:
                        logger.info(f"Thermostat {device_id} set to {payload['temperature']}°C")
                        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {msg.payload.decode()}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def publish_sensor_data(self, temperature, humidity):
        """Publish sensor data to MQTT broker"""
        payload = json.dumps({
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            self.client.publish(TOPIC_TEMP, payload)
            logger.info(f"Published sensor data to {TOPIC_TEMP}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish sensor data: {e}")
            return False
            
    def control_device(self, device_type, device_id, state):
        """Control a smart home device"""
        topic = f"home/devices/{device_type}/{device_id}"
        payload = json.dumps({"state": state})
        
        try:
            self.client.publish(topic, payload)
            logger.info(f"Sent command to {topic}: {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to control device: {e}")
            return False

def send_alert(temperature, humidity):
    """Send an alert notification (simulated)"""
    logger.warning(f"ALERT! Temperature threshold exceeded: {temperature:.1f}°C")
    
    # In a real system, you would send an SMS, push notification, or email
    # For this example, we'll just print the alert and save to the database
    print(f"🚨 ALERT: Temperature ({temperature:.1f}°C) exceeds threshold of {TEMP_THRESHOLD}°C!")
    print(f"Current humidity: {humidity:.1f}%")
    
    # For demo purposes, you could also publish an alert via MQTT
    try:
        publish.single(
            "home/alerts/temperature",
            json.dumps({
                "alert_type": "high_temperature",
                "temperature": temperature,
                "humidity": humidity,
                "threshold": TEMP_THRESHOLD,
                "timestamp": datetime.now().isoformat()
            }),
            hostname=MQTT_BROKER,
            port=MQTT_PORT
        )
        return True
    except Exception as e:
        logger.error(f"Failed to publish alert: {e}")
        return False

def main():
    """Main function to run the smart home controller"""
    logger.info("Starting Smart Home Controller")
    
    # Initialize components
    sensor = SmartHomeSensor()
    database = Database(DB_PATH)
    mqtt_controller = MQTTController(MQTT_BROKER, MQTT_PORT)
    
    # Connect to MQTT broker
    if not mqtt_controller.connect():
        logger.error("Failed to connect to MQTT broker. Exiting.")
        return
    
    # Main loop
    try:
        while True:
            # Read sensor data
            temperature = sensor.read_temperature()
            humidity = sensor.read_humidity()
            
            # Check if threshold is exceeded
            alert_triggered = temperature > TEMP_THRESHOLD
            
            # Store reading in database
            database.store_reading(temperature, humidity, alert_triggered)
            
            # Publish to MQTT
            mqtt_controller.publish_sensor_data(temperature, humidity)
            
            # Send alert if needed
            if alert_triggered:
                send_alert(temperature, humidity)
                
                # Example: Automatically adjust thermostat if temperature is too high
                if temperature > TEMP_THRESHOLD:
                    mqtt_controller.control_device("thermostat", "living_room", "on")
                    target_temp = min(temperature - 2, 22)  # Aim for 2 degrees lower, max 22°C
                    mqtt_controller.publish_sensor_data(
                        target_temp, 
                        humidity
                    )
            
            # Wait before next reading
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Smart Home Controller stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Clean up
        mqtt_controller.client.loop_stop()
        logger.info("Smart Home Controller shut down")

if __name__ == "__main__":
    main()
