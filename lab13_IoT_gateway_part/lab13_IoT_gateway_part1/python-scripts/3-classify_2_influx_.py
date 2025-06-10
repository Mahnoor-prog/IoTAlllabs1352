import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import tensorflow as tf
import numpy as np
import time
from datetime import datetime, timezone

# InfluxDB setup
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-influxdb-t"  # Replace with your token
INFLUXDB_ORG = "my-org"  # Replace with your org
INFLUXDB_BUCKET = "My bucket"  # Replace with your bucket

# MQTT setup
MQTT_BROKER = "192.168.100.142"
MQTT_PORT = 1883
MQTT_TOPIC_TEMP = "esp32/dht/temp"
MQTT_TOPIC_HUM = "esp32/dht/hum"


# Class names
class_names = [
    "Normal",
    "Hot and Humid",
    "Cold and Dry",
    "Hot and Dry",
    "Cold and Humid"
]

# Load model and normalization data
model = tf.keras.models.load_model("dht_classifier.h5")
norm_data = np.load("normalization.npz")
X_min = norm_data["min"]
X_max = norm_data["max"]

# MQTT and InfluxDB clients
mqtt_client = mqtt.Client()
influxdb_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

temperature = None
humidity = None

def on_message(client, userdata, msg):
    global temperature, humidity
    try:
        if msg.topic == MQTT_TOPIC_TEMP:
            temperature = float(msg.payload.decode())
            print(f" Received Temperature: {temperature:.2f}°C")
        elif msg.topic == MQTT_TOPIC_HUM:
            humidity = float(msg.payload.decode())
            print(f" Received Humidity: {humidity:.2f}%")

        # Only process when both temperature and humidity are received
        if temperature is not None and humidity is not None:
            # Normalize input
            X_input = np.array([[temperature, humidity]])
            X_norm = (X_input - X_min) / (X_max - X_min)

            # Predict class
            pred_probs = model.predict(X_norm, verbose=0)
            predicted_class = np.argmax(pred_probs)
            class_label = class_names[predicted_class]

            print(f" Predicted Class: {class_label}")

            # Timestamp in UTC
            now = datetime.utcnow().replace(tzinfo=timezone.utc)

            # Prepare InfluxDB point (store class_label as a tag, not a field)
            point = (
                Point("dht_data")
                .tag("device", "esp32")
                .tag("class_label", class_label)
                .field("temperature", temperature)
                .field("humidity", humidity)
                .time(now)
            )

            print(f" Writing to InfluxDB: {point.to_line_protocol()}")
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)

            print(f" Data saved: Temp={temperature:.2f}, Hum={humidity:.2f}, Class={class_label}")

            # Reset for next reading
            temperature = None
            humidity = None

    except Exception as e:
        print(f" Error processing message: {e}")

def on_connect(client, userdata, flags, rc):
    print(f"🔗 Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_TEMP)
    client.subscribe(MQTT_TOPIC_HUM)

# Setup MQTT callbacks and connect
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to MQTT broker...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(" Exiting gracefully...")
finally:
    mqtt_client.loop_stop()
    influxdb_client.close()
