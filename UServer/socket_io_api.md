##  [LoRaWAN](http://183.230.40.231:8100) - SocketIO API Reference

This file will introduce you the data form of our API.

Socket.IO 1.0

	For test:

    ws://183.230.40.231:8100/test,{query:'app_eui=be7a009fbe7a0000&token=pMJv-1cBL7XOEFQh9OoEHQ'}

## Data Form



#### Event: 'rx'

    Direction: Server to Client
    Description: The data passed over to the various APIs transport layers are always JSON formatted.
                 Every JSON message you receive corresponds to one frame produced by your device.
    Data Format:

    {
        cmd      : 'rx';	// UPDATED! identifies type of message, rx = uplink message
        EUI      : string;  // device EUI, 16 hex digits (without dashes)
        ts       : number;  // server timestamp as number (miliseconds from Linux epoch)
        fcnt     : number;  // frame counter, a 32-bit number
        port     : number;  // port as sent by the end device
        encdata? : string;  // data payload (APPSKEY encrypted)
                            // only present if APPSKEY is assigned to device
                            // string format based on application setup (default is hex string)
        data?    : string;  // data payload
                            // only present if APPSKEY is not assigned to device
                            // string format based on application setup (default is hex string)
        // extended radio information
        freq     : number;  // radio frequency
        dr       : string;  // radio data rate - spreading factor, bandwidth and coding rate
                            // e.g. SF12 BW125 4/5
        rssi     : number;  // radio rssi
        snr      : number;  // radio snr
    }


#### Event: 'tx' 

    Direction: Client to Server(Sending plain text)
    Data Format:

    {
        cmd      : 'tx';	// must always have the value 'tx'
        EUI      : string;  // device EUI, 16 hex digits (without dashes)
        port     : number;  // port to be used (1..223)
        data     : string;  // data payload (to be encrypted by our server)
                            // if no APPSKEY is assigned to device, this will return an error
                            // string format based on application setup (default is hex string)
        rx_window?: number; // choose rx window 1 or rx window2, if not present, default rx window will be used.
                               for class a device is rx1, for class c device is rx2. 
        confirmed? : Bool;  // if confirmed set to be True, message type will be Confirmed Message
    }
 
    Direction: Client to Server(Sending cipher text)
    Data Format:
    {
        cmd      : 'tx';	// must always have the value 'tx'
        EUI      : string;  // device EUI, 16 hex digits (without dashes)
        port     : number;  // port to be used (1..223)
        seqno    : seqno;   // seqno of this message;
                            // seqno = fcnt + len(queue);
                            // if the seqno does not match,
                            // server will return an error with the expected seqno
        encdata  : string;  // data payload (already APPSKEY encrypted)
                            // the payload has to be encrypted using the latest downlink sequence number
                            // string format based on application setup (default is hex string)
        rx_window?: number; // choose rx window 1 or rx window2, if not present, default rx window will be used.
                       for class a device is rx1, for class c device is rx2. 
        confirmed? : Bool;  // if confirmed set to be True, message type will be Confirmed Message
    }

    Direction: Client to Server(Sending plain Multicast Message to a multicast group of devices)
    Data Format:
    {
        cmd      : 'mtx';	// must always have the value 'tx'
        EUI      : string;  // Multicast Group EUI, 16 hex digits (without dashes)
        port     : number;  // port to be used (1..223)
        data     : string;  // data payload (to be encrypted by our server)
                            // if no APPSKEY is assigned to device, this will return an error
                            // string format based on application setup (default is hex string)
    }

    Direction: Client to Server(Sending cipher Multicast Message to a multicast group of devices)
    Data Format:
    {
        cmd      : 'mtx';	// must always have the value 'tx'
        EUI      : string;  // Multicast Group EUI, 16 hex digits (without dashes)
        port     : number;  // port to be used (1..223)
        seqno    : seqno;   // seqno of this message; seqno = fcnt + len(queue);
                            // if the seqno does not match,
                            // server will return an error with the expected seqno;
        encdata  : string;  // data payload (already APPSKEY encrypted)
                            // the payload has to be encrypted using the latest downlink sequence number
                            // string format based on application setup (default is hex string)
    }


#### Event: 'ack_tx'
    Direction: Server to Client
    Description: Acknowledgment of send request
    Data Format:
    {
        cmd      : 'tx' or 'mtx';	// always has the value 'tx'(unicast) or 'mtx'(multicast)
        EUI      : string;          // device EUI, 16 hex digits (without dashes)
        success? : Bool;            // if command succeeded, will be present and will contain a confirming string.
        error?   : string;          // string describing the encountered error
                                    // only present if the command failed
        data?    : string;          // data that was enqueued (either plaintext or ciphertext)
                                    // only present if the command succeeded
    }


#### Event: 'confirm_tx'
    Direction: Server to Client
    Description: Confirm the packet has been sent to gateway for delivery
    Data Format:
    {
        cmd      : 'txd' or 'mtxd';	// always has the value 'txd'(unicast) or 'mtxd'(multicast)
        EUI      : string;          // device EUI, 16 hex digits (without dashes)
        fcnt    : number;           // sequence number used for the downlink
        ts       : number;          // unix timestamp, moment of the transfer to the gateway
    }


#### Event: 'cache_query'
    Direction:  Client to Server
    Description:
    Data Format:
    {
        cmd      : 'cache_query';	    // identifies type of message, cq = cache query
        filter?   : {
            start_ts?   : number;       // filter messages from this timestamp
            end_ts?     : number;       // filter messages up to this timestamp
            dev_eui?    : string;       // filter only messages from this EUI
            app_eui?    : string;
        },
        page_num? : number;              // page indicator (one-based), default 1
        per_page? : number;              // results to return per page, default 100
    }

    Direction: Server to Client
    Description: send back the required data
    Data Format:
    {
        cmd      : 'cache_query';	    // identifies type of message, cq = cache query
        filter?   : {                   // repeats query filter
            start_ts?   : number;
            end_ts?     : number;
            dev_eui?    : string;
            app_eui?    : string;
        },
        page_num : number;              // repeats query page
        per_page : number;              // repeats query perPage
        total    : number;              // total number of matching results in cache
                                        // use for paging through history
        cache    : list;                // list of cached messages, ordered by descending timestamp
                                        // format corresponds to your selected Data Format / verbosity
                                        // if gateway information output is enabled,
                                        // only 'gw' messages will be returned
    }

#### Event: 'abp_req'
    Direction: Client to Server
    Description: 
    Data Format:
    {
        cmd     :   'abp_req';
        name?   :   string;
        dev_eui :   string;
        app_eui :   string;
        dev_addr:   string;     //little endian
        nwkskey :   string;
    }

    Direction: Server to Client
    Description:
    Data Format:
    {
        cmd     :   'abp_req';
        dev_eui?:   string;
        success :   0 or 1;     //0:fail,1:success
        error?  :   string;
    }

#### Event: 'mac_cmd'
    Direction: Client to Server
    Description:
    Data Format:
    {
        cmd     :   'mac_cmd';
        dev_eui :   string;
        mac_cmd :   string;     // cid+mac_cmd_payload;
                                // eg:	'0331ff0101' means cid = 0x03,payload = 31ff0101;
                                //      means ADR set device to data_rate = 'SF9BW125',
                                //      tx_power = 14dBm,
                                //      chMask set 9 channel;
    }

    Direction:      Server to Client
    Description:
    Data Format:
    {
        cmd     :   'mac_cmd';
        dev_eui?:   string;
        success :   0 or 1;
        error?  :   string;
    }

