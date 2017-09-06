from const import Const, MType
from struct import pack
from utils.lora_crypto import LoRaCrypto
from struct import unpack
from object.group import Group
from object.device import Device, ClassType
from object.retransmission import Resend
from utils.log import logger, ConstLog
from utils.utils import endian_reverse
from binascii import hexlify


class DownLinkUni(object):
    def __init__(self, device, mtype, fpending, ack, adrackreq, mac_command, cipher, fport, frmpayload):
        self.device = device
        self.mtype = mtype
        self.fpending = fpending
        self.ack = ack
        self.adrackreq = adrackreq
        self.mac_command = mac_command
        self.cipher = cipher
        self.fport = fport
        self.frmpayload = frmpayload

    def pack_data(self):
        # device = Device.objects.get(self.dev_eui)
        addr_int = unpack(">I", self.device.addr)[0]
        frmpayload = b''
        if self.cipher is not None:
            if self.fport == 0:
                frmpayload = LoRaCrypto.payload_encrypt(self.frmpayload, self.device.nwkskey, addr_int, Const.DIR_DOWN, self.device.fcnt_down)
                frmpayload = bytes([self.fport]) + frmpayload
            elif 0 < self.fport < 256:
                if self.cipher == 0:
                    appskey = self.device.appskey
                    if appskey == b'':
                        logger.error(ConstLog.txpk + " PLAINTEXT NEED TO BE SEND BUT NO APPSKEY SET")
                    else:
                        frmpayload = LoRaCrypto.payload_encrypt(self.frmpayload, appskey, addr_int, Const.DIR_DOWN, self.device.fcnt_down)
                        frmpayload = bytes([self.fport]) + frmpayload
                elif self.cipher == 1:
                    frmpayload = self.frmpayload
                    frmpayload = bytes([self.fport]) + frmpayload
        fcnt = self.device.fcnt_down & 0x0000ffff
        mac_fhdr_fcnt = pack('<I', fcnt)[0:2]
        mac_fhdr_fctrl_foptslen = len(self.mac_command)
        assert mac_fhdr_fctrl_foptslen <= 15, 'AssertError: Mac Command over length '
        mac_fhdr_fopts = self.mac_command
        mac_fhdr_fctrl_adr = int(self.device.adr)

        mhdr = bytes([Const.MAJOR_LORA | (Const.MHDR_RFU << 2) | (self.mtype << 5)])
        fctrl = bytes([mac_fhdr_fctrl_foptslen | (self.fpending << 4) |
                       (self.ack << 5) | (self.adrackreq << 6) | (mac_fhdr_fctrl_adr << 7)])
        fhdr = endian_reverse(self.device.addr) + fctrl + mac_fhdr_fcnt + mac_fhdr_fopts
        phypayload = mhdr + fhdr + frmpayload
        mic = LoRaCrypto.compute_mic(phypayload, self.device.nwkskey, addr_int, Const.DIR_DOWN, self.device.fcnt_down)
        phypayload = phypayload + mic
        if self.mtype == MType.CONFIRMED_DATA_DOWN:
            Resend(self.device.dev_eui).set_resend_data(phypayload)
        return phypayload


class DownLinkMulti(object):
    def __init__(self, group, fpending, text_type, fport, frmpayload):
        """
        :param group: Group
        :param fpending:
        :param text_type:
        :param fport:
        :param frmpayload:
        :param fcnt_int:
        :return:
        """
        assert isinstance(group, Group), 'GROUP ERROR'
        assert fpending == 0 or fpending == 1, 'FPENDING ERROR'
        assert text_type == 0 or text_type == 1 or text_type is None, 'TEXT TYPE ERROR'
        if text_type is not None:
            assert isinstance(fport, int) and 0 <= fport < 256, 'FPORT ERROR'
            assert isinstance(frmpayload, bytes), 'FRMPAYLOAD ERROR'
        self.group = group
        self.fpending = fpending
        self.text_type = text_type
        self.fport = fport
        self.frmpayload = frmpayload

    def pack_data(self):
        addr_int = unpack(">I", self.group.addr)[0]
        frmpayload = b''
        if self.text_type is not None:
            if self.text_type == 0:
                if self.fport == 0:
                    key = self.group.nwkskey
                elif 0 < self.fport < 256:
                    key = self.group.appskey
                    if key == b'':
                        logger.error(ConstLog.txpk + " PLAINTEXT NEED TO BE SEND BUT NO APPSKEY SET")
                frmpayload = LoRaCrypto.payload_encrypt(self.frmpayload, key, addr_int, Const.DIR_DOWN, self.group.fcnt)
            elif self.text_type == 1:
                frmpayload = self.frmpayload
            frmpayload = bytes([self.fport]) + frmpayload

        fcnt = self.group.fcnt & 0x0000ffff
        mac_fhdr_fcnt = pack('<I', fcnt)[0:2]
        mac_fhdr_fopts = b''
        mac_fhdr_fctrl_foptslen = 0
        mac_fhdr_fctrl_adr = 0
        ack = 0
        adrackreq = 0
        mtype = MType.UNCONFIRMED_DATA_DOWN

        mhdr = bytes([Const.MAJOR_LORA | (Const.MHDR_RFU << 2) | (mtype << 5)])
        fctrl = bytes([mac_fhdr_fctrl_foptslen | (self.fpending << 4) |
                       (ack << 5) | (adrackreq << 6) | (mac_fhdr_fctrl_adr << 7)])
        fhdr = endian_reverse(self.group.addr) + fctrl + mac_fhdr_fcnt + mac_fhdr_fopts

        phypayload = mhdr + fhdr + frmpayload
        mic = LoRaCrypto.compute_mic(phypayload, self.group.nwkskey, addr_int, Const.DIR_DOWN, self.group.fcnt)
        phypayload = phypayload + mic
        return phypayload



