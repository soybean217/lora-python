class Const:
    CONFIG_IDENTIFIER = b'\x05'
    CONFIG_RESP_IDENTIFIER = b'\x06'
    CONIG_UPG = b'\x07'

    PROTOCOL_VERSION = 1
    UNUSED_BYTE = b'\x00'

    PROTOCOL_VERSION_1 = 1  # CN470_510的为V1版本配置文件, 不分包
    PROTOCOL_FRAG_VERSION_2 = 2  # CN470_510的V1版本配置文件, 发送时候, 分包发送
    PROTOCOL_FRAG_VERSION_3 = 3  # CN470_510的更新为V2版本配置文件, 发送时候, 分包发送

    PROTOCOL_FRAG_SET = [PROTOCOL_FRAG_VERSION_2, PROTOCOL_FRAG_VERSION_3]

    LAST_FW_VER_DEFAULT = {
        'RPI': '2.1.0',
        'BBB': '2.1.0'
    }
    LAST_FW_VER_RPI = 'RPI' + '.' + LAST_FW_VER_DEFAULT['RPI']
    LAST_FW_VER_BBB = 'BBB' + '.' + LAST_FW_VER_DEFAULT['BBB']
    LAST_FW_VER_SET = [LAST_FW_VER_BBB, LAST_FW_VER_RPI]
    LAST_FW_VER_PATH = {
        'RPI': 'lora-ftp/RPI/',
        'BBB': 'lora-ftp/BBB/'
    }
    LAST_FW_VER_NAME = 'lora_pkt_fwd'

