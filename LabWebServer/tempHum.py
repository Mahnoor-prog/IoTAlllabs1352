import dht
import machine
import time

# Change GPIO4 to another pin if needed (e.g., GPIO5)
DHT_PIN = 4  

# Initialize DHT11 sensor
sensor = dht.DHT11(machine.Pin(DHT_PIN))

while True:
    try:
        sensor.measure()  # Take a measurement
        temp = sensor.temperature()  # Read temperature (°C)
        hum = sensor.humidity()  # Read humidity (%)
        
        print("Temperature:", temp, "°C")
        print("Humidity:", hum, "%")

    except OSError as e:
        print("DHT11 sensor error. Check wiring.", e)

    time.sleep(2)  # Wait for 2 seconds before the next reading
