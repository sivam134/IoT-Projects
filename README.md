# Simple Smart Home System

A lightweight Python-based smart home system that monitors temperature and humidity, controls smart devices, and sends alerts when thresholds are exceeded.

## Features

- Temperature and humidity monitoring
- MQTT-based device communication
- SQLite database for data storage
- Automated alerts when temperature exceeds threshold
- Control for lights, thermostats, and door locks

## Project Structure

```
simple-smart-home/
├── smart_home_controller.py  # Main application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .env.example              # Example environment variables
```

## Requirements

- Python 3.6+
- MQTT Broker (like Mosquitto)
- SQLite

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/simple-smart-home.git
   cd simple-smart-home
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy the environment file and customize as needed:
   ```
   cp .env.example .env
   ```

4. Install and configure an MQTT broker:

   ### Windows Installation
   1. Download the Mosquitto installer from the official website:
      - Go to https://mosquitto.org/download/
      - Click on the Windows installer link (typically "mosquitto-2.x.x-install-windows-x64.exe")
   
   2. Run the installer:
      - Accept the license agreement
      - Choose installation location
      - Complete the installation
   
   3. Configure Mosquitto:
      - Open Notepad as Administrator
      - Open the file `C:\Program Files\mosquitto\mosquitto.conf`
      - Add these lines at the end of the file to allow connections:
        ```
        listener 1883
        allow_anonymous true
        ```
      - Save the file
   
   4. Start the Mosquitto service:
      - Open Command Prompt as Administrator
      - Run: `net start mosquitto`
      - Alternatively, you can set it to start automatically through Windows Services
   
   5. Verify installation:
      - Open Command Prompt
      - Run: `mosquitto_sub -h localhost -t test`
      - In another Command Prompt window, run: `mosquitto_pub -h localhost -t test -m "hello"`
      - You should see "hello" appear in the first window

   ### Linux Installation (Ubuntu/Debian)
   ```
   sudo apt install mosquitto mosquitto-clients
   sudo systemctl enable mosquitto
   sudo systemctl start mosquitto
   ```

## Usage

Run the main controller script:

```
python smart_home_controller.py
```

### Controlling Devices

You can control devices by publishing MQTT messages to the appropriate topics:

#### Windows
```
# Control a light
mosquitto_pub -h localhost -t "home/devices/lights/living_room" -m "{\"state\": \"on\"}"

# Set thermostat
mosquitto_pub -h localhost -t "home/devices/thermostat/bedroom" -m "{\"state\": \"on\", \"temperature\": 22.5}"

# Control door lock
mosquitto_pub -h localhost -t "home/devices/lock/front_door" -m "{\"state\": \"locked\"}"
```

Note: On Windows Command Prompt, you need to escape the quotes with backslashes.

#### Linux/macOS
```
# Control a light
mosquitto_pub -h localhost -t "home/devices/lights/living_room" -m '{"state": "on"}'

# Set thermostat
mosquitto_pub -h localhost -t "home/devices/thermostat/bedroom" -m '{"state": "on", "temperature": 22.5}'

# Control door lock
mosquitto_pub -h localhost -t "home/devices/lock/front_door" -m '{"state": "locked"}'
```

### Viewing Data

The system stores all sensor readings in the SQLite database. You can query it using:

#### Windows
```
# If you have SQLite installed
sqlite3 smart_home.db "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 10;"

# Alternatively, you can use DB Browser for SQLite
# Download from: https://sqlitebrowser.org/dl/
```

#### Linux/macOS
```
sqlite3 smart_home.db "SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 10;"
```

## Extending the System

### Adding New Sensors

1. Create a new sensor class or extend the existing one
2. Add the appropriate reading function
3. Update the main loop to collect and store the new sensor data

### Adding New Devices

1. Add a new topic constant for the device type
2. Update the MQTT subscription in the `on_connect` method
3. Extend the `on_message` handler to process commands for the new device

## Troubleshooting

### Windows-specific Issues

1. **Mosquitto service won't start**:
   - Check if port 1883 is already in use by another application
   - Verify your mosquitto.conf file has the correct syntax
   - Check Windows Event Viewer for specific error messages

2. **Cannot connect to MQTT broker**:
   - Ensure Windows Firewall allows connections on port 1883
   - Verify the Mosquitto service is running with `sc query mosquitto`

3. **Python can't find the paho-mqtt library**:
   - Ensure you've installed the requirements with the correct pip for your Python environment
   - Try running `pip install paho-mqtt` separately

## Security Considerations

For a production environment, consider implementing:

- TLS encryption for MQTT communications
- Authentication for device control
- Secure storage of sensitive data
- Network segmentation for IoT devices

