import machine
import dht
import ssd1306
import neopixel
import network
import socket
import utime

# Wi-Fi Credentials
SSID = "A"
PASSWORD = "qwertyuiop"

# GPIO Pins
DHT_PIN = 5  # Changed to avoid conflict (choose any free GPIO)
LED_PIN = 48  # Built-in Neopixel LED (check your board's documentation)
OLED_SDA = 8
OLED_SCL = 9

# Initialize DHT11 Sensor
dht_sensor = dht.DHT11(machine.Pin(DHT_PIN))

# Built-in Neopixel LED Setup (1 pixel)
np = neopixel.NeoPixel(machine.Pin(LED_PIN), 1)

# Initialize I2C & OLED Display
i2c = machine.I2C(0, scl=machine.Pin(OLED_SCL), sda=machine.Pin(OLED_SDA))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Function to Set Neopixel LED Color
def set_led_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

# Connect to Wi-Fi in STA Mode & Start AP Mode
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(SSID, PASSWORD)

ap_if = network.WLAN(network.AP_IF)
ap_if.active(True)
ap_if.config(essid="ESP32_AP", password="12345678")

# Wait for Connection
while not sta_if.isconnected() and not ap_if.active():
    utime.sleep(1)

print("STA IP:", sta_if.ifconfig()[0])
print("AP IP:", ap_if.ifconfig()[0])

# HTML Web Page
html = """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 RGB & Sensor Control</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; }
        input { width: 50px; }
        button { margin: 10px; padding: 10px; background: green; color: white; }
    </style>
</head>
<body>
    <h2>ESP32 RGB LED Control</h2>
    <label>Red:</label> <input type="number" id="r" min="0" max="255">
    <label>Green:</label> <input type="number" id="g" min="0" max="255">
    <label>Blue:</label> <input type="number" id="b" min="0" max="255">
    <button onclick="sendRGB()">Set Color</button>

    <h2>Temperature & Humidity</h2>
    <p id="temp">Temperature: --°C</p>
    <p id="hum">Humidity: --%</p>

    <h2>OLED Message</h2>
    <input type="text" id="message">
    <button onclick="sendMessage()">Display</button>

    <script>
        function sendRGB() {
            var r = document.getElementById("r").value;
            var g = document.getElementById("g").value;
            var b = document.getElementById("b").value;
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/rgb?r="+r+"&g="+g+"&b="+b, true);
            xhr.send();
        }
        
        function sendMessage() {
            var msg = document.getElementById("message").value;
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/message?text=" + encodeURIComponent(msg), true);
            xhr.send();
        }
        
        setInterval(function() {
            fetch('/sensor')
            .then(response => response.json())
            .then(data => {
                document.getElementById("temp").innerText = "Temperature: " + data.temp + "°C";
                document.getElementById("hum").innerText = "Humidity: " + data.hum + "%";
            });
        }, 5000);
    </script>
</body>
</html>
"""

# Web Server Function
def web_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    
    while True:
        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode()
            print("Request received:", request)

            response = ""

            # Handle RGB LED Control
            if "/rgb?" in request:
                try:
                    params = request.split(" ")[1].split("?")[1]
                    param_dict = dict(x.split("=") for x in params.split("&"))
                    
                    r = int(param_dict.get("r", 0))
                    g = int(param_dict.get("g", 0))
                    b = int(param_dict.get("b", 0))
                    
                    set_led_color(r, g, b)
                    response = "HTTP/1.1 200 OK\nContent-Type: text/plain\n\nLED Updated"
                except Exception as e:
                    print("RGB Parsing Error:", str(e))
                    response = "HTTP/1.1 400 Bad Request\n\nInvalid RGB Values"

            # Handle Sensor Data Request
            elif "/sensor" in request:
                try:
                    dht_sensor.measure()
                    temp = dht_sensor.temperature()
                    hum = dht_sensor.humidity()
                    
                    oled.fill(0)
                    oled.text("Temp: {} C".format(temp), 10, 20)
                    oled.text("Humidity: {}%".format(hum), 10, 40)
                    oled.show()
                    
                    response = 'HTTP/1.1 200 OK\nContent-Type: application/json\n\n'
                    response += '{"temp": ' + str(temp) + ', "hum": ' + str(hum) + '}'
                
                except Exception as e:
                    print("Error Processing Sensor Request:", str(e))
                    response = "HTTP/1.1 500 Internal Server Error\n\nSensor Error"

            # Handle OLED Display Message
            elif "/message?" in request:
                try:
                    msg = request.split(" ")[1].split("?")[1].split("=")[1]
                    msg = msg.replace("%20", " ")  # Handle spaces
                    oled.fill(0)
                    oled.text(msg, 10, 30)
                    oled.show()
                    response = "HTTP/1.1 200 OK\nContent-Type: text/plain\n\nMessage Displayed"
                except Exception as e:
                    print("OLED Error:", str(e))
                    response = "HTTP/1.1 400 Bad Request\n\nInvalid Message"

            # Serve Web Page
            else:
                response = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + html

            conn.send(response.encode())  # Ensure encoding before sending
            conn.close()

        except Exception as e:
            print("Server Error:", str(e))
            conn.close()  # Close connection in case of error

# Start the server
web_server()




