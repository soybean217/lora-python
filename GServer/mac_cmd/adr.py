from mac_cmd.mac_cmd_gen import LinkADRReqPayload, MACCmd, CID
from utils.log import Logger, Action, IDType
from threading import Thread
import time
from object.trans_params import TransParams
from object.gateway import Gateway
from gevent import Greenlet
import gevent
from frequency_plan import frequency_plan
from binascii import hexlify


def shift_to(dev_eui, datr, FREQ_PLAN):
    payload = LinkADRReqPayload(data_rate=datr,
                                tx_power=FREQ_PLAN.TXPower.default.value,
                                ch_mask=FREQ_PLAN.Channel.CH_MASK,
                                ch_mask_cntl=FREQ_PLAN.Channel.CH_MASK_CNTL,
                                nb_trans=FREQ_PLAN.Channel.NB_TRANS).return_data()
    mac_cmd_down = MACCmd(dev_eui)
    mac_cmd_down.push_into_que(CID.LinkADRReq, payload=payload)
    Logger.info(action=Action.adr, type=IDType.device, id=hexlify(dev_eui).decode(), msg="shift to %s" % datr)


def adr_base_on_rssi(device):
    gateway = Gateway.objects.best_mac_addr(device.dev_eui)
    tran_params = TransParams.objects.get(device.dev_eui, gateway.mac_addr)
    FREQ_PLAN = frequency_plan[device.app.freq_plan]
    recent_datr = FREQ_PLAN.DataRate[tran_params['datr']].value
    required_datr = FREQ_PLAN.adr_schema(tran_params['rssi'], recent_datr)
    if recent_datr != required_datr:
        shift_to(device.dev_eui, required_datr, FREQ_PLAN)


def adr_base_on_pk_stg(device):
    mac_addr = Gateway.objects.best_mac_addr(device.dev_eui)
    if mac_addr is None:
        Logger.error(action=Action.adr, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg="Gateway.objects.best_mac_addr return None")
        return
    tran_params = TransParams.objects.get(device.dev_eui, mac_addr)
    pk_stg = float(tran_params['rssi']) + float(tran_params['lsnr']) * 0.25
    FREQ_PLAN = frequency_plan[device.app.freq_plan]
    recent_datr = FREQ_PLAN.DataRate[tran_params['datr']].value
    required_datr = FREQ_PLAN.adr_schema(pk_stg, recent_datr)
    if recent_datr < required_datr:
        shift_to(device.dev_eui, recent_datr + 1, FREQ_PLAN)
    elif recent_datr > required_datr:
        shift_to(device.dev_eui, recent_datr - 1, FREQ_PLAN)
    else:
        Logger.info(action=Action.adr, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg="do not need to shift")

# class ADR(Thread):
#     def __init__(self,db,dev_eui):
#         self.db = db
#         self.dev_eui = dev_eui
#         Thread.__init__(self,daemon=True)
#
#     def run(self):
#         time.sleep(1)
#         adr_base_on_pk_stg(self.db,self.dev_eui)


class ADR(Greenlet):
    def __init__(self, device):
        self.device = device
        Greenlet.__init__(self)

    def _run(self):
        # gevent.sleep(1)
        adr_base_on_pk_stg(self.device)