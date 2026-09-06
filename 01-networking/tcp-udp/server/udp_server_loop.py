import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('0.0.0.0', 5001))
print("UDP loop server listening on port 5001...")

count = 0
while True:
    data, addr = server.recvfrom(4096)
    count += 1
    print(f"Received #{count} from {addr}: {data.decode()}")
    server.sendto(f"ack {count}".encode(), addr)
