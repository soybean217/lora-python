from binascii import a2b_base64, hexlify, unhexlify
from base64 import urlsafe_b64decode
from datetime import datetime
import pytz


def is_primitive(data):
    return isinstance(data, (int, bool, float, str))


def validate_number(data):
    try:
        return float(data)
    except ValueError:
        return False


def eui_64_to_48(eui_64):
    assert len(eui_64) == 8, eui_64[3] == 255 and eui_64[4] == 255
    eui_48 = eui_64[:3] + eui_64[5:]
    return eui_48


def eui_48_to_64(eui_48):
    assert len(eui_48) == 6, 'Except EUI-48 but got %s' % eui_48
    eui_64 = eui_48[:3] + b'\xff\xff' + eui_48[3:]
    return eui_64


def base64_decode(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += '='*missing_padding
    try:
        bytes_data = a2b_base64(data)
        return bytes_data
    except Exception as error:
        raise error


def base64_decode_urlsafe(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += '='*missing_padding
    try:
        bytes_data = urlsafe_b64decode(data)
        return bytes_data
    except Exception as error:
        raise error


def display_hex_hyphen(byte_data, byteorder='big'):
    if isinstance(byte_data, str):
        byte_data = unhexlify(byte_data)
    str_addr = ''
    if byteorder == 'little':
        for byte in byte_data:
            str_addr = '-' + hexlify(bytes([byte])).decode().upper() + str_addr
    elif byteorder == 'big':
        for byte in byte_data:
            str_addr = str_addr + '-' + hexlify(bytes([byte])).decode().upper()
    return str_addr.lstrip('-')


def display_hex(byte_data, byteorder='big'):
    if isinstance(byte_data, str):
        byte_data = unhexlify(byte_data)
    str_addr = ''
    if byteorder == 'little':
        for byte in byte_data:
            str_addr = hexlify(bytes([byte])).decode().upper() + str_addr
    elif byteorder == 'big':
        str_addr = hexlify(byte_data).decode().upper()
    return str_addr


def ts_to_iso(timestamp):
    utc_dt = datetime.fromtimestamp(timestamp)
    return utc_dt.replace(tzinfo=pytz.timezone('Etc/GMT+8')).isoformat()


# if __name__ == '__main__':
#     a = b'\x01\x02\x03\xff\xff\x11\x11\x11\x11'
#     print(eui_64_to_48(a))
#     print(a)