class MACConst:
    link_check_req = 'LinkCheckReo'
    link_adr_ans = 'LinkADRAns'
    duty_cycle_ans = 'DutyCycleAns'
    rx_param_ans = 'RXParamSetupAns'
    dev_status_ans = 'DevStatusAns'
    new_ch_ans = 'NewChannelAns'
    rx_timing_ans = 'RXTimingSetupAns'

    battery = 'battery'
    snr = 'snr'

    mac_cmd_up_len = {
        2: 0,
        3: 1,
        4: 0,
        5: 1,
        6: 2,
        7: 1,
        8: 0,
        10: 1,
        11: 1,
        12: 0,
        13: 1,
        16: 1,
        17: 1,
        18: 0,
        19: 1,
    }
