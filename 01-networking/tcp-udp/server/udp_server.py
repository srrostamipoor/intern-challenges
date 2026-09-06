import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('0.0.0.0', 5001))
print("UDP server is listening on port 5001...")

data,addr = server.recvfrom(4096)
print(f"Received from {addr}: {data.decode()}")

server.sendto("Hello from UDP server!".encode(),addr)

server.close()
