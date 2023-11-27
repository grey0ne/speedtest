import socket
import sys
from timeit import default_timer as timer
from time import sleep
import math
import os.path
import random
from dataclasses import dataclass
from typing import Tuple

server_port = 10000

UNIT_LIST = ['', 'K', 'M', 'G']

MESSAGE_LENGTHS = [100000, 100000, 1000000, 1000000, 3000000, 3000000, 6000000, 6000000]
RECEIVE_BUFFER = 255
PING_REPEATS = 10

TERMINATION_SYMBOL = 255
CONNECT_TIMEOUT = 0.2
SEND_TIMEOUT = 10

DOWNLOAD_MESSAGE_LENGTH = 10


@dataclass
class TestResult:
    message_length: int
    duration: float


def get_socket(server_address: Tuple[str, int]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)

    try:
        sock.connect(server_address)
    except TimeoutError:
        print(f'Connect timeout {CONNECT_TIMEOUT} seconds to {server_address}')
        sock.close()
        return
    return sock


def receive_bytes(sock, expected_length):
    amount_received = 0
    while amount_received < expected_length:
        data = sock.recv(RECEIVE_BUFFER)
        amount_received += len(data)


def test_upload(server_address: Tuple[str, int], message_length: int) -> Tuple[TestResult, TestResult]:
    message = generate_message(message_length)
    amount_expected = 1
    
    sock = get_socket(server_address)

    if sock is None:
        return

    sock.settimeout(SEND_TIMEOUT)
    start = timer()
    try:
        sock.sendall(message)
        receive_bytes(sock, amount_expected) 
    except TimeoutError:
        print(f'Send timeout {SEND_TIMEOUT} seconds')
        return
    finally:
        sock.close()


    return TestResult(len(message), timer() - start)


def get_scaled_unit(data_size: int) -> Tuple[str, float]:
    log = int(math.log(data_size, 1000))
    return UNIT_LIST[log], data_size if log == 0 else data_size / (1000 ** log)


def show_timings(test_result: TestResult, process_name: str) -> None:
    data_size = test_result.message_length * 8
    data_unit, data_size_scaled = get_scaled_unit(data_size)
    
    speed = data_size / test_result.duration
    unit, speed_scaled = get_scaled_unit(speed)
    
    highSpeed = test_result.message_length / test_result.duration
    high_unit, highSpeed_scaled = get_scaled_unit(highSpeed)
    
    status = f"{process_name} {data_size_scaled:.2f} {data_unit}bits of data in {test_result.duration * 1000:.2f} ms."
    status += f" {speed_scaled:.2f} {unit}bps"
    print(status)


def generate_message(length):
    arr = []
    for x in range(length - 1):
        arr.append(random.choice(range(TERMINATION_SYMBOL - 1)).to_bytes(1))
    result = b''.join(arr)
    return result + TERMINATION_SYMBOL.to_bytes(1)


def client(server):
    print(f'Connecting to {server} on port: {server_port}')

    server_address = (server, server_port)

    for x in range(PING_REPEATS): 
        result = test_upload(server_address, 1)
        print(f'Ping {result.duration * 1000:.2f} ms')
        
    for message_length in MESSAGE_LENGTHS: 
        up_result = test_upload(server_address, message_length)
        show_timings(up_result, 'Up  ')


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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = get_local_server_address()
   
    server_address = (server_address, server_port)
    print(f'starting up on {server_address} port {server_port}')
    sock.bind(server_address)

    sock.listen(1)

    try:
        while True:
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
                if len(message) == DOWNLOAD_MESSAGE_LENGTH + 1:
                    #testing download
                    message_length = int.from_bytes(message[:-1])
                    message = generate_message(message_length)
                    connection.sendall(message)
                else:
                    #testing upload
                    message = generate_message(1)
                    connection.sendall(message)
            finally:
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
