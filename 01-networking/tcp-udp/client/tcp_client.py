import socket

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(('tcp-server', 5000))
print("Connected to server")

client.send("Hello from TCP client!".encode())

data = client.recv(4096)
print(f"Received: {data.decode()}")

client.close()
