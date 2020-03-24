import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Bind the socket to the port
server_address = ('0.0.0.0', 5000)
print(f'starting up on {server_address[0]} port {server_address[1]}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)


        while True:
            data = connection.recv(1024)
            print('Received: ')
            print(data)
            if not data: break

        print('sending response to server')
        response = 'HTTP/1.1 200 OK'
        connection.sendall(response.encode())

    finally:
        # Clean up the connection
        connection.close()
