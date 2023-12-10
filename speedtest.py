import socket
import sys
from timeit import default_timer as timer
import math
import os.path
import random
from dataclasses import dataclass
from typing import Tuple

SERVER_PORT = 10000

UNIT_LIST = ['', 'K', 'M', 'G']

MESSAGE_LENGTH = 10000000
DOWNLOAD_REPS = 20
UPLOAD_REPS = DOWNLOAD_REPS
RECEIVE_BUFFER = 1000
PING_REPEATS = 50

TERMINATION_SYMBOL = 255
CONNECT_TIMEOUT = 0.2
SEND_TIMEOUT = 10

DOWNLOAD_MESSAGE_LENGTH = 10

def generate_message(length):
    arr = []
    for _ in range(length):
        arr.append(random.choice(range(TERMINATION_SYMBOL - 1)).to_bytes(1))
    result = b''.join(arr)
    return result

BASE_MESSAGE = generate_message(10000)

@dataclass
class TestResult:
    message_length: int
    duration: float


class SpeedTestException(Exception):
    pass


def connect_socket(sock, server_address):
    sock.settimeout(CONNECT_TIMEOUT)

    try:
        sock.connect(server_address)
    except TimeoutError as e:
        print(f'Connect timeout {CONNECT_TIMEOUT} seconds to {server_address}')
        raise e
    return sock


def receive_bytes(sock:socket.socket, expected_length: int):
    amount_received = 0
    while amount_received < expected_length:
        data = sock.recv(RECEIVE_BUFFER)
        amount_received += len(data)


def test_upload(sock: socket.socket, message_length: int) -> TestResult:
    amount_expected = 1

    start = timer()
    send_bytes(sock, message_length, amount_expected)

    return TestResult(message_length, timer() - start)


def send_bytes(sock: socket.socket, message_length: int, response_length: int):
    sock.settimeout(SEND_TIMEOUT)
    try:
        for _ in range(int(message_length / len(BASE_MESSAGE))):
            sock.sendall(BASE_MESSAGE)
        sock.sendall(TERMINATION_SYMBOL.to_bytes(1))
        receive_bytes(sock, response_length)
    except TimeoutError as e:
        print(f'Send timeout {SEND_TIMEOUT} seconds')
        raise e


def send_message(sock: socket.socket, message: bytes, response_length: int):
    sock.settimeout(SEND_TIMEOUT)
    try:
        sock.sendall(message)
        receive_bytes(sock, response_length)
    except TimeoutError as e:
        print(f'Send timeout {SEND_TIMEOUT} seconds')
        raise e


def generate_download_message(message_length: int) -> bytes:
    return message_length.to_bytes(DOWNLOAD_MESSAGE_LENGTH) + TERMINATION_SYMBOL.to_bytes(1)


def test_dowload(sock: socket.socket, message_length: int) -> TestResult:
    message = generate_download_message(message_length)
    amount_expected = message_length

    start = timer()
    send_message(sock, message, amount_expected)

    return TestResult(len(message), timer() - start)


def end_session(sock: socket.socket):
    message = TERMINATION_SYMBOL.to_bytes(1) * 2

    try:
        sock.sendall(message)
    except TimeoutError as e:
        print(f'Send timeout {SEND_TIMEOUT} seconds')
        raise e


def get_scaled_unit(data_size: float) -> Tuple[str, float]:
    log = int(math.log(data_size, 1000))
    return UNIT_LIST[log], data_size if log == 0 else data_size / (1000 ** log)


def show_timings(test_result: TestResult, process_name: str) -> None:
    data_size = test_result.message_length * 8
    data_unit, data_size_scaled = get_scaled_unit(data_size)

    speed = data_size / test_result.duration
    unit, speed_scaled = get_scaled_unit(speed)

    status = f"{process_name} {data_size_scaled:.2f} {data_unit}bits of data in {test_result.duration * 1000:.2f} ms."
    status += f" {speed_scaled:.2f} {unit}bps"
    print(status)

def show_aggregates(result_list):
    min_speed = 0

def init_client(server):
    print(f'Connecting to {server} on port: {SERVER_PORT}')

    server_address = (server, SERVER_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            connect_socket(sock, server_address)
            ping_results = []
            for _ in range(PING_REPEATS):
                result = test_upload(sock, 1)
                print(f'Ping {result.duration * 1000:.2f} ms')
<<<<<<< HEAD
            up_results = []
            for message_length in MESSAGE_LENGTHS:
                up_result = test_upload(sock, message_length)
                up_results.append(up_result)
=======
            for _ in range(UPLOAD_REPS):
                up_result = test_upload(sock, MESSAGE_LENGTH)
>>>>>>> 9a5d32801b092fbbb3eebdd97e12969b50c25a89
                show_timings(up_result, 'Up  ')
            show_aggregates(up_results)
            end_session(sock)
        except TimeoutError:
            pass


def get_local_server_address():
    # The most convinient way to determine local ip, without knowing network interface name
    server_address = 'localhost'
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(('8.8.8.8', 80))
            server_address = sock.getsockname()[0]
        except TimeoutError:
            pass
    return server_address


def process_connection(connection, client_address):
    while True:
        try:
            data_size = 0
            start = timer()
            while True:
                try:
                    data = connection.recv(RECEIVE_BUFFER)
                except ConnectionResetError:
                    print(f'Client dropped connection {client_address[0]}')
                    return
                data_size += len(data)
                if len(data) == 0 or data[-1] == TERMINATION_SYMBOL:
                    break
            if data_size == DOWNLOAD_MESSAGE_LENGTH + 1:
                # Testing download
                message_length = int.from_bytes(data[:-1])
                print(f'Sending {message_length} bytes to {client_address[0]}')
                start = timer()
                message = generate_message(message_length)
                print(f'Message generation time {(timer() - start) * 1000:.2f} ms')
                connection.sendall(message)
            elif data_size == 2 and data[0] == TERMINATION_SYMBOL:
                # End session
                connection.close()
                print(f'Client {client_address[0]} session ended')
                break
            else:
                print(f'Received {data_size} bytes from {client_address[0]} during {(timer() - start) * 1000:.2f} ms')
                # Testing upload
                message = generate_message(1)
                try:
                    connection.sendall(message)
                except BrokenPipeError:
                    print('Cannot send response')
                    return
        except TimeoutError:
            pass


def init_server():
    server_ip = get_local_server_address()
    server_address = (server_ip, SERVER_PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        print(f'starting up on {server_ip} port {SERVER_PORT}')
        sock.bind(server_address)

        sock.listen(1)

        while True:
            connection, client_address = sock.accept()
            print(f'Connection from {client_address[0]}')
            process_connection(connection, client_address)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['/?', '-help', '--help']:
        bin_path = os.path.basename(sys.argv[0])
        print(f"Usage: {bin_path} [server IP] If server is not specified, {bin_path} will open a port to act as the server")
        sys.exit(0)

    server_address = 'localhost'
    if len(sys.argv) > 1:
        server_address = sys.argv[1]
        init_client(server_address)
    else:
        init_server()

if __name__ == '__main__':
    main()
