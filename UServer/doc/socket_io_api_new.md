##  [LoRaWAN](http://183.230.40.231:8300) - SocketIO API Reference

This file will introduce you the data form of our API.

[Socket.IO 1.0](http://socket.io/)




	For test:

    http://183.230.40.231:8300/test?app_eui=be7a009fbe7a0000&token=pMJv-1cBL7XOEFQh9OoEHQ

## Data Form



#### Event: 'post_rx'

    Direction: Server to Client
    Description: The data passed over to the various APIs transport layers are always JSON formatted.
                 Every JSON message you receive corresponds to one frame produced by your device.
    Data Format:

    {
        EUI      : string;  // device EUI, 16 hex digits (without dashes)
        ts       : number;  // server timestamp as number (miliseconds from Linux epoch)
        fcnt     : number;  // frame counter, a 32-bit number
        port     : number;  // port as sent by the end device
        encrypt  : boolean; // if APPSKEY is assigned to device, encrypt will be false, data is decrypted by appskey, 
                               else encrypt will be false and data is still encrypted by appskey
        data? : string;  // data payload. string format based on hex string
                         // extended radio information
        freq     : number;  // radio frequency
        datr     : string;  // radio data rate - spreading factor, bandwidth and coding rate
                            // e.g. SF12 BW125 4/5
        rssi     : number;  // radio rssi
        lsnr      : number; // radio lsnr
    }



#### Event: 'tx' 

    Direction: Client to Server(Sending plain text)
    Data Format:

    {
        type     : string;  // multicast or unicast
        EUI      : string;  // device EUI or Group ID, 16 hex digits (without dashes)
        port     : number;  // port to be used (1..223)
        data     : string;  // data payload (to be encrypted by our server)
        cipher   : boolean; // if data is encrypted by appskey, cipher should be true, else cipher should be flase.
                            // if cipher is **false** and **NO** APPSKEY is assigned to device, this will return an error.
                            // if cipher is **true** and **seqno** is not appeared, this will return an error.
        seqno?   : seqno;   // only required when cipher is true.
                            // seqno is the fcnt you use to encrypt this data. It should match the expected seqno, 
                            // seqno = fcnt + len(queue);
                            // if the seqno does not match, this will return an error.
        rx_window? : number; // choose rx window 1 or rx window2, if not present, default rx window will be used.
                             // for class a device is rx1, for class c device is rx2. 
        confirmed? : Bool;   // if confirmed set to be True, message type will be Confirmed Message
        nonce?     : number or string; // if nonce is present, ack_tx and confirm_tx will carry along the same nonce 
    }


#### Event: 'ack_tx'
    Direction: Server to Client
    Description: Acknowledgment of send request
    Data Format:
    {
        type     : 'unicast' or 'multicast';	// always has the value 'tx'(unicast) or 'mtx'(multicast)
        EUI      : string;           // device EUI, 16 hex digits (without dashes)
        success? : string;           // if command succeeded, will be present and will contain a confirming string.
                                     // only present if the command succeeded
        error?   : string;           // string describing the encountered error
                                     // only present if the command failed
        data?    : string;           // data that was enqueued (either plaintext or ciphertext)
                                     // only present if the command succeeded
        nonce?   : number or string; // corresponding to nonce in event tx
    }


#### Event: 'confirm_tx'
    Direction: Server to Client
    Description: Confirm the packet has been sent to gateway for delivery
    Data Format:
    {
        type            : 'unicast' or 'multicast';	// always has the value 'txd'(unicast) or 'mtxd'(multicast)
        EUI             : string;          // device EUI, 16 hex digits (without dashes)
        fcnt            : number;           // sequence number used for the downlink
        ts              : number;          // unix timestamp, moment of the transfer to the gateway
        retransmission: : 
        nonce           : number or string; // corresponding to nonce in event tx
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
        cache    : array;               // array of cached messages, ordered by descending timestamp
                                        // format corresponds to your selected Data Format / verbosity
                                        // if gateway information output is enabled,
                                        // only 'gw' messages will be returned
    }


