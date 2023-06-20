import argparse
import logging
import time
from datetime import datetime

import crcmod as crcmod

logging.basicConfig(filename=f"clockSetting{datetime.now().strftime('%m%d%y')}.log",
                    format='%(asctime)s %(message)s',
                    filemode='a',
                    level=logging.INFO)


def connect(ip):
    connect_message = bytes(
        [0x47, 0x54, 0xc0, 0x15, 0x01, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xcf, 0x79])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 7000))
    sock.sendto(connect_message, (ip, 7000))
    logging.info(f"Contacted clock: {connect_message.hex()}")

    wait_for_response(sock)

    return sock


def wait_for_response(sock):
    data, addr = sock.recvfrom(7000)
    logging.info(f"Received confirmation: {data.hex()}")


def send_message(sock, ip, plain_message):
    full_message = create_full_message(plain_message)

    sock.sendto(full_message, (ip, 7000))
    logging.info(f"Sent display text: {full_message.hex()}")

    wait_for_response(sock)


def create_full_message(plain_message):
    message_head = bytes([0x47, 0x54, 0x80, 0x24, 0x0b, 0, 0])  # GT $

    # max message length is 32, plus another 0 between it and the checksum
    message_to_send = message_head + bytes(plain_message, 'utf-8') + b'\0' * (33 - len(plain_message))
    crc16 = crcmod.mkCrcFun(0x18005, initCrc=0xFFFF)

    return message_to_send + crc16(message_to_send).to_bytes(2, 'little')


def get_args_as_list():
    CLI = argparse.ArgumentParser()
    CLI.add_argument("ips", nargs="+")
    CLI.add_argument("message")
    return CLI


# usage: CoIP.py 192.168.200.192 127.0.0.1 "Mincha 8:10PM"
if __name__ == '__main__':
    args = get_args_as_list().parse_args()

    for address in args.ips:
        logging.info(f"***STARTING CLOCK @ {address}***")
        socket = connect(address)
        time.sleep(.5)
        send_message(socket, address, args.message)  # todo add timeout
        logging.info(f"***FINISHED CLOCK***")
