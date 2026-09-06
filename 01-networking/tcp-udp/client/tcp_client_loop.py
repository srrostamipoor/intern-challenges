import socket
import time

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('tcp-server', 5000))
print("Connected to server")

count = 0
while True:
    count += 1
    client.send(f"message {count}".encode())
    data = client.recv(4096)
    print(f"Sent message {count}, got: {data.decode()}")
    time.sleep(2)
