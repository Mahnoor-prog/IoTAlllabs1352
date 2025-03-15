import network
import socket
import dht
import machine
import ssd1306  # OLED library

# WiFi Configuration
SSID = "Noor"
PASSWORD = "12345678"

# Initialize WiFi in Station Mode
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    pass  # Wait for connection

print("Connected! IP Address:", wifi.ifconfig()[0])

# Initialize DHT11 Sensor
dht_pin = machine.Pin(4)  # GPIO4
dht_sensor = dht.DHT11(dht_pin)

# Initialize OLED Display (SSD1306)
i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))  
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Initialize RGB LED (Built-in NeoPixel)
from neopixel import NeoPixel  # Import NeoPixel library

rgb_pin = machine.Pin(48, machine.Pin.OUT)  # Change pin if needed
rgb_led = NeoPixel(rgb_pin, 1)  # Only 1 LED on ESP32

# Function to Set RGB Color
def set_rgb_color(r, g, b):
    rgb_led[0] = (r, g, b)
    rgb_led.write()

# Function to Read Temperature & Humidity
def get_sensor_data():
    dht_sensor.measure()
    temp = dht_sensor.temperature()
    hum = dht_sensor.humidity()
    return temp, hum

# Function to Update OLED Display
def update_oled(temp, hum, r, g, b):
    oled.fill(0)  # Clear screen
    oled.text("Temp: {} C".format(temp), 0, 0)
    oled.text("Humidity: {}%".format(hum), 0, 10)
    oled.text("RGB: R{} G{} B{}".format(r, g, b), 0, 30)
    oled.show()

# HTML Web Page
def generate_webpage(temp, hum):
    return f""" 
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ESP32 Web Server</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }}
            .container {{ width: 80%; margin: auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            input {{ padding: 10px; font-size: 16px; width: 60px; margin: 5px; text-align: center; }}
            button {{ padding: 10px 20px; font-size: 18px; margin-top: 10px; cursor: pointer; background: #007BFF; color: white; border: none; border-radius: 5px; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ESP32 RGB LED & Sensor Web Server</h1>
            <h2>Temperature: {temp}°C</h2>
            <h2>Humidity: {hum}%</h2>

            <h3>Set RGB Color</h3>
            <form action="/" method="GET">
                <input type="number" name="r" placeholder="Red (0-255)" min="0" max="255">
                <input type="number" name="g" placeholder="Green (0-255)" min="0" max="255">
                <input type="number" name="b" placeholder="Blue (0-255)" min="0" max="255">
                <br>
                <button type="submit">Set Color</button>
            </form>
        </div>
    </body>
    </html>
    """

    
    

# Start Web Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 80))
server.listen(5)

print("Web Server Started! Access it via browser.")

while True:
    conn, addr = server.accept()
    print("Client connected from", addr)
    
    request = conn.recv(1024).decode()
    
    # Parse RGB Values
    r, g, b = 0, 0, 0  # Default values
    if "GET /?" in request:
        try:
            params = request.split(" ")[1].split("?")[1].split("&")
            r = int(params[0].split("=")[1])
            g = int(params[1].split("=")[1])
            b = int(params[2].split("=")[1])
            set_rgb_color(r, g, b)
        except:
            pass
    
    # Get Sensor Data
    temp, hum = get_sensor_data()

    # Update OLED Display
    update_oled(temp, hum, r, g, b)

    # Send Webpage Response
    response = generate_webpage(temp, hum)
    conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + response)
    conn.close()
