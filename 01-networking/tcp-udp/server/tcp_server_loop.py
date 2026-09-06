import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 5000))
server.listen(1)
print("TCP loop server listening on port 5000...")

conn, addr = server.accept()
print(f"Connected by {addr}")

count = 0
while True:
    data = conn.recv(4096)
    if not data:
        break
    count += 1
    print(f"Received #{count}: {data.decode()}")
    conn.send(f"ack {count}".encode())
