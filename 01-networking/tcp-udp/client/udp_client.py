import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.sendto("Hello from UDP client!".encode(),('tcp-server',5001))

data, addr = client.recvfrom(4096)
print(f"Received from {addr}: {data.decode()}")

client.close()
