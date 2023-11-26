import socket
import sys
from timeit import default_timer as timer
import math
import os.path
import random

server_port = 10000

unit_list = ['', 'K', 'M', 'G']

MESSAGE_LENGTH = 1000000
RECEIVE_BUFFER = 255

TERMINATION_SYMBOL = 255
CONNECT_TIMEOUT = 0.1
SEND_TIMEOUT = 10
RECEIVE_TIMEOUT = 10

def ping(sock, message):
    # Send data
    amount_expected = len(message)
    start = timer()
    print(f'Message length {amount_expected} bytes')

    sock.settimeout(SEND_TIMEOUT)
    try:
        sock.sendall(message)
    except TimeoutError:
        print(f'Send timeout {TIMEOUT} seconds')
        sock.close()
        return
    
    amount_received = 0
    sock.settimeout(RECEIVE_TIMEOUT)
    while amount_received < amount_expected:
        try:
            data = sock.recv(RECEIVE_BUFFER)
        except TimeoutError:
            print(f'Receive timeout {TIMEOUT} seconds')
            sock.close()
            return
        if amount_received == 0 and len(data) > 0:
            upload_end = timer()
            show_timings(amount_expected, upload_end - start, 'Upload')
        amount_received += len(data)
    show_timings(amount_expected, timer() - upload_end, 'Download')


def get_scaled_unit(data_size):
    log = int(math.log(data_size, 1000))
    return unit_list[log], data_size if log == 0 else data_size / (1000 ** log)


def show_timings(message_size, duration, process_name):
    data_size = message_size * 8 # char to bits
    data_unit, data_size_scaled = get_scaled_unit(data_size)
    
    speed = data_size / duration
    unit, speed_scaled = get_scaled_unit(speed)
    
    highSpeed = message_size / duration
    high_unit, highSpeed_scaled = get_scaled_unit(highSpeed)
    
    print(f"{process_name} {data_size_scaled:.2} {data_unit}bits of data in {duration:.2} seconds")
    print(f"{speed_scaled:.2f} {unit}bps or {highSpeed_scaled:.2} {high_unit}Bps")


def generate_message(length):
    arr = []
    for x in range(MESSAGE_LENGTH):
        arr.append(random.choice(range(TERMINATION_SYMBOL - 1)).to_bytes(1))
    result = b''.join(arr)
    return result + TERMINATION_SYMBOL.to_bytes(1)


def client(server):
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
        
    server_address = (server, server_port)
    print(f'Connecting to {server} on port: {server_port}')
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect(server_address)
    except TimeoutError:
        print(f'Connect timeout {TIMEOUT} seconds to {server_address}')
        sock.close()
        return
    message = generate_message(MESSAGE_LENGTH)

    ping(sock, message)
    sock.close()


def get_local_server_address():
    # The most convinient way to determine local ip, without knowing network interface name
    server_address = 'localhost'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        server_address = s.getsockname()[0]
    except:
        pass
    return server_address


def server():
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # get local IP address by connecting to Google
    server_address = get_local_server_address()
   
    # Bind the socket to the port
    server_address = (server_address, server_port)
    print(f'starting up on {server_address} port {server_port}')
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    try:
        while True:
            # Wait for a connection
            print('Waiting for a connection')
            connection, client_address = sock.accept()
            try:
                print(f'Connection from {client_address}')

                data_size = 0
                message = b''
                while True:
                    data = connection.recv(RECEIVE_BUFFER)
                    data_size += len(data)
                    message += data
                    if data[-1] != TERMINATION_SYMBOL:
                        print(f'Received {data_size} from {client_address}')
                    else:
                        print(f'No more data from {client_address}')
                        break
                connection.sendall(message)
            finally:
                # Clean up the connection
                connection.close()
    except Exception as e:
        sock.close()
        raise


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ['/?', '-help', '--help']:
        bin_path = os.path.basename(sys.argv[0])
        print(f"Usage: {bin_path} [server IP] If server is not specified, {bin_path} will open a port to act as the server")
        sys.exit(0)

    server_address = 'localhost'
    if len(sys.argv) > 1:
        server_address = sys.argv[1]
        client(server_address)
    else:
       server()
