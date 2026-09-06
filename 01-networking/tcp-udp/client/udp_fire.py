import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client.sendto("Fire and forget!".encode(), ('tcp-server', 5001))
print("Message sent. Not waiting for any reply.")

client.close()
