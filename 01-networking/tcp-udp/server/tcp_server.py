import socket

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5000))
server.listen(1)
print("TCP server is listening on port 5000...")

conn,addr = server.accept()
print(f"connected by {addr}")

data = conn.recv(4096)
print(f"Received: {data.decode()}")

conn.send("Hello from TCP server!".encode())
conn.close()
