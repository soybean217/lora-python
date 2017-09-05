from struct import pack, unpack

MAX_SCALE = 2.0**23
LONGITUDE = 180
LATITUDE = 90


def pack_longitude(longitude):
    """
    :param longitude: float
    :return:
    """
    longitude = int(longitude / LONGITUDE * MAX_SCALE)
    # print('pack', longitude)
    # longitude = pack('>i', longitude)
    # print('pack', longitude)
    return longitude


def pack_latitude(latitude):
    """
    :param longitude: float
    :return:
    """
    print('lat ',latitude)
    latitude = int(latitude / LATITUDE * MAX_SCALE)
    print('lat ', latitude)
    # print('pack', longitude)
    # longitude = pack('>i', longitude)
    # print('pack', longitude)
    return latitude


def unpack_longitude(longitude):
    """
    :param longitude: 3 bytes signed int
    :return:
    """
    assert isinstance(longitude, bytes) and len(longitude) == 3
    sign = longitude[0] >> 7
    if sign == 0:
        append = b'\x00'
    else:
        append = b'\xff'
    longitude = unpack('>i', append + longitude)[0]
    # print(longitude)
    longitude = longitude / (MAX_SCALE - 1) * LONGITUDE
    # print(longitude)
    return longitude