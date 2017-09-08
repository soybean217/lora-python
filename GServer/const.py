from enum import IntEnum


class Const:

    JOIN_SERVER_ADDR = ('localhost', 8800)
    DIR_UP = 0
    DIR_DOWN = 1

    GATEWAY_CONFIG_IDENTIFIER = b'\x05'
    GATEWAY_CONFIG_RESQ_IDENTIFIER = b'\x06'

    # PROTOCOL_VERSION = b'\x01'
    PUSH_DATA_IDENTIFIER = 0x00
    PUSH_ACK_IDENTIFIER = b'\x01'
    PULL_DATA_IDENTIFIER = 0x02
    PULL_RESP_IDENTIFIER = b'\x03'
    PULL_ACK_IDENTIFIER = b'\x04'
    TX_ACK_IDENTIFIER = 0X05

    UNUSED_BYTE = b'\x00'

    MHDR_RFU = 0B000

    MAJOR_LORA = 0B00

    MAX_FCNT_GAP = 16384

    MTypes = {0b000: 'Join Request',
              0b001: 'Join Accept',
              0b010: 'Unconfirmed Data Up',
              0b011: 'Unconfirmed Data Dwon',
              0b100: 'Confirmed Data Up',
              0b101: 'Confirmed Data Down',
              0b110: 'RFU',
              0b111: 'Proprietary'}

    Major = {0b00: 'LoRaWAN R1',
             0b01: 'RFU',
             0b10: 'RFU',
             0b11: 'RFU'}

    MAX_RESEND_NUM = 8

    IGNORE_DATA = b'\x00'
    PROCESS_DATA = b'\x01'

    EU868_MAX_PAYLOAD_LEN = 51

    CONNECTION_TIMEOUT = 60


class MType(IntEnum):
    JOIN_REQUEST = 0B000
    JOIN_ACCEPT = 0B001
    UNCONFIRMED_DATA_UP = 0B010
    UNCONFIRMED_DATA_DOWN = 0B011
    CONFIRMED_DATA_UP = 0B100
    CONFIRMED_DATA_DOWN = 0B101
    RFU = 0B110
    PTY = 0B111  # Proprietary


class EU863_870:
    DataRate = {
        0: 'SF12BW125',
        1: 'SF11BW125',
        2: 'SF10BW125',
        3: 'SF9BW125',
        4: 'SF8BW125',
        5: 'SF7BW125',
        6: 'SF7BW250',
    }
    BEACON_FREQ = 869.525

if __name__ == '__main__':
    print(MType.UNCONFIRMED_DATA_DOWN.value)
    print(MType.UNCONFIRMED_DATA_DOWN - 1)