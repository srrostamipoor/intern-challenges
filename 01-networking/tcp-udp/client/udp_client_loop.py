import socket
import time

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

count = 0
while True:
    count += 1
    client.sendto(f"message {count}".encode(), ('tcp-server', 5001))
    data, addr = client.recvfrom(4096)
    print(f"Sent message {count}, got: {data.decode()}")
    time.sleep(2)
