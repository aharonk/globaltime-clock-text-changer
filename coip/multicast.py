import logging
import socket
import time
from datetime import datetime

import crcmod as crcmod

logging_enabled = False

PORT = 7001
CONNECT_MESSAGE = bytes(
    [0x47, 0x54, 0xc0, 0x15, 0x01, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xcf, 0x79])
MESSAGE_HEAD = bytes([0x47, 0x54, 0x80, 0x24, 0x0b, 0, 0])  # GT $

SOCK = None


def multicast(ips, message, timeout, log=True):
    try:
        get_socket_instance()
    except OSError:
        return "Only one instance of the program can run at once."

    set_log(log)

    failed_IPs = []

    for address in ips:
        logging.info(f"***STARTING CLOCK @ {address}***")
        if connect_to_clock(address, timeout):
            time.sleep(.5)
            send_message(address, message)
        else:
            failed_IPs.append(address)
        logging.info("***FINISHED CLOCK***")

    return "Run Successful." if not failed_IPs else (
            "The following addresses did not respond:\n" + ('\n'.join(failed_IPs)))


def get_socket_instance():
    global SOCK
    if not SOCK:
        SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        SOCK.bind(('', PORT))


def set_log(do_log):
    global logging_enabled

    if do_log:
        if not logging_enabled:
            logging_enabled = True
            logging.basicConfig(filename=f"clockSetting{datetime.now().strftime('%m%d%y')}.log",
                                format='%(asctime)s %(message)s',
                                filemode='a',
                                level=logging.INFO)
        logging.disable(logging.NOTSET)
    else:
        logging.disable(logging.INFO)


def connect_to_clock(ip, timeout):
    SOCK.settimeout(timeout)
    SOCK.sendto(CONNECT_MESSAGE, (ip, PORT))

    logging.info(f"Contacted clock: {CONNECT_MESSAGE.hex()}")

    return wait_for_response()


def wait_for_response():
    try:
        data, addr = SOCK.recvfrom(PORT)
        logging.info(f"Received confirmation: {data.hex()}")
        return True
    except TimeoutError:
        logging.info("Timed out waiting for response.")
        return False


def send_message(ip, plain_message):
    full_message = create_full_message(plain_message)

    SOCK.sendto(full_message, (ip, PORT))
    logging.info(f"Sent display text: {full_message.hex()}")

    wait_for_response()


def create_full_message(plain_message):
    # max message length is 32, plus another 0 between it and the checksum
    message_to_send = MESSAGE_HEAD + bytes(plain_message, 'utf-8') + b'\0' * (33 - len(plain_message))
    crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF)

    return message_to_send + crc16(message_to_send).to_bytes(2, 'little')
