from ctypes import CDLL, c_uint8, c_uint32,  create_string_buffer, byref
import os


class LoRaCrypto:
    if os.name == 'nt':
        sys_path = 'D:\lora_server\GServer'
        Crypto = CDLL(sys_path + "\DLLs\LoRaMacCrypto.dll")
    else:
        Crypto = CDLL("./lora_encrypt/libloraCrypto.so")
        # initial_dir = os.getcwd()
        # os.chdir('/home/gaozhi/GServer/www/')
        # Crypto = CDLL("./lora_encrypt/libloraCrypto.so")
        # os.chdir(initial_dir)

    @staticmethod
    def compute_mic(msg, key, address, dir, sequenceCounter):
        mic = (c_uint32 * 1)()
        LoRaCrypto.Crypto.LoRaMacComputeMic(create_string_buffer(msg),
                                            c_uint8(len(msg)),
                                            create_string_buffer(key),
                                            c_uint32(address),
                                            c_uint8(dir),
                                            c_uint32(sequenceCounter),
                                            byref(mic))
        return bytes(mic)

    @staticmethod
    def payload_encrypt(buffer, key, address, dir, sequenceCounter):
        enBuffer = (c_uint8 * len(buffer))()
        LoRaCrypto.Crypto.LoRaMacPayloadEncrypt(create_string_buffer(buffer),
                                                c_uint8(len(buffer)),
                                                create_string_buffer(key),
                                                c_uint32(address),
                                                c_uint8(dir),
                                                c_uint32(sequenceCounter),
                                                byref(enBuffer))
        # print('encryptbuffer:',hexlify(bytes(enBuffer)[:len(buffer)]).decode())
        return bytes(enBuffer)

    @staticmethod
    def payload_decrypt(encbuffer, key, address, dir, sequenceCounter):
        Buffer = (c_uint8 * len(encbuffer))()
        LoRaCrypto.Crypto.LoRaMacPayloadDecrypt(create_string_buffer(bytes(encbuffer)),
                                          c_uint8(len(encbuffer)),
                                          create_string_buffer(bytes(key)),
                                          c_uint32(address),
                                          c_uint8(dir),
                                          c_uint32(sequenceCounter),
                                          byref(Buffer))
        # print('dncryptbuffer result:',hexlify(bytes(Buffer)[:len(encbuffer)]).decode())
        return bytes(Buffer)

    @staticmethod
    def join_compute_skey(key, appNonce, devNonce):
        '''
        :param key: bytes 16
        :param appNonce: bytes 3
        :param devNonce: bytes 2
        :return:
        '''
        nwkSKey = (c_uint8 * 16)()
        appSKey = (c_uint8 * 16)()
        devnonce = int.from_bytes(devNonce, byteorder='little')
        LoRaCrypto.Crypto.LoRaMacJoinComputeSKeys(create_string_buffer(key),
                                                  create_string_buffer(appNonce),
                                                  c_uint8(devnonce),
                                                  byref(nwkSKey),
                                                  byref(appSKey))
        return bytes(nwkSKey), bytes(appSKey)

    @staticmethod
    def join_compute_mic(join_request, key):
        mic = (c_uint32 * 1)()
        LoRaCrypto.Crypto.LoRaMacJoinComputeMic(create_string_buffer(join_request),
                                                c_uint8(len(join_request)),
                                                create_string_buffer(key),
                                                byref(mic))
        return bytes(mic)

    @staticmethod
    def join_encrypt(clear,key):
        cypher = (c_uint8 * len(clear))()
        LoRaCrypto.Crypto.LoRaMacJoinEncrypt(create_string_buffer(bytes(clear)),
                                             c_uint8(len(clear)),
                                             create_string_buffer(bytes(key)),
                                             byref(cypher))
        # print('encryptbuffer result:',hexlify(bytes(cypher)).decode())
        return bytes(cypher)

    @staticmethod
    def join_decrypt(cypher,key):
        clear = (c_uint8 * len(cypher))()
        LoRaCrypto.Crypto.LoRaMacJoinDecrypt(create_string_buffer(bytes(cypher)),
                                             c_uint8(len(cypher)),
                                             create_string_buffer(bytes(key)),
                                             byref(clear))
        # print('decryptbuffer result:',hexlify(bytes(clear)).decode())
        return bytes(clear)

    @staticmethod
    def ping_rand_compute(key, beacon_time, dev_addr):
        enBuffer = (c_uint8 * 16)()
        LoRaCrypto.Crypto.LoRaPingRandencrypt(
                                          create_string_buffer(key),
                                          c_uint32(beacon_time),
                                          c_uint32(dev_addr),
                                          byref(enBuffer))
        return bytes(enBuffer)

    # void LoRaMacJoinDecrypt( uint8_t *buffer, uint16_t size, const uint8_t *key, uint8_t *decBuffer );
    #
    # void LoRaMacJoinEncrypt(uint8_t *buffer, uint16_t size, const uint8_t *key, uint8_t *decBuffer);

if __name__ == '__main__':
    # frampayload = b'\xaf\xa0\r\x9fp>'
    # appskey = b'#\xc4\xcd\n\x8e\xb8\x93\x03G$q\xbbc\x906\n'
    # addr_int = 1939865614
    # DIR_UP = 0
    # fcnt = 6
    # plain_text = LoRaCrypto.payload_decrypt(frampayload, appskey, addr_int, DIR_UP, fcnt)
    # print(plain_text)
    from binascii import a2b_base64, hexlify
    import binascii

    def base64_decode(data):
        missing_padding = 4 - len(data) % 4
        if missing_padding:
            data += '=' * missing_padding
        try:
            return a2b_base64(data)
        except binascii.Error as error:
            raise error
            return None


    data = base64_decode("gA4AcImAAQDycpx+oEjC1A==")
    print(data)
    print(hexlify(data[1:5]))
    dev_addr = int.from_bytes(data[1:5], byteorder='little')
    print(dev_addr)
    mic = data[len(data)-4:]
    nwkskey = b'\xfc\n\x83\xb7\xab\x04\xaa\xa0\x14\x94u\x8b\xea\xcf\x97:'
    fcnt = 1
    addr = 2305818638
    dir_up = 0
    mic_compute = LoRaCrypto.compute_mic(data[0:len(data)-4], nwkskey, addr, dir_up, fcnt)
    print()
    print('mic', mic)
    print('mic_compute', mic_compute)