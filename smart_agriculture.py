import time
import numpy as np
from datetime import datetime

MOISTURE_THRESHOLD = 30  # % threshold
SIMULATION_MODE = True

class SoilMonitor:
    def read_sensors(self):
        moisture = np.random.uniform(20, 60) if SIMULATION_MODE else 45
        temperature = np.random.uniform(18, 30) if SIMULATION_MODE else 22
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Moisture: {moisture:.1f}%, Temp: {temperature:.1f}°C")
        return moisture

    def check_irrigation(self, moisture):
        return moisture < MOISTURE_THRESHOLD

    def notify_user(self, msg):
        print(f"📢 {msg}")

def main():
    monitor = SoilMonitor()
    try:
        while True:
            moisture = monitor.read_sensors()
            if monitor.check_irrigation(moisture):
                monitor.notify_user("Irrigation Needed!")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
