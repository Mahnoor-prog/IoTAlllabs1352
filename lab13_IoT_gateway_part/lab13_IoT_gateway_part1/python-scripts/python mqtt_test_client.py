import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.disconnect()

client = mqtt.Client()
client.on_connect = on_connect
client.connect("192.168.100.142", 1883, 60)
client.loop_forever()
