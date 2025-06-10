import socket

broker_ip = "localhost"  # or "192.168.100.142"
broker_port = 1883

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((broker_ip, broker_port))
if result == 0:
    print(f"Port {broker_port} on {broker_ip} is open!")
else:
    print(f"Cannot connect to port {broker_port} on {broker_ip}")
sock.close()
