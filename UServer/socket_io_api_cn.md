##  [LoRaWAN](http://183.230.40.231:8100) - SocketIO API Reference

本文档将想您介绍LoRaWAN服务器接口的数据格式。

Socket.IO 1.0

	For test:

    ws://183.230.40.231:8100/test,{query:'app_eui=be7a009fbe7a0000&token=pMJv-1cBL7XOEFQh9OoEHQ'}

## 数据格式

    传输到SocketIO接口传输层的数据必须是JSON格式。

#### Event: 'rx'

    方向: 服务器到客户端
    描述: 您接收到的每一个JSON数据包都对应着终端设备的一个上行数据帧。
    数据格式:

    {
        cmd      : 'rx';	// 数据包的类型标识, rx = 上行数据
        EUI      : string;  // 设备EUI, 16位十六进制数(不包括横杠)
        ts       : number;  // 服务器收到上行数据的时间戳 (毫秒)
        fcnt     : number;  // 帧计数器数, 为一个32为无符号整数
        port     : number;  // 设备发送数据的端口
        encdata? : string;  // data payload (没有APPSKEY解密的密文)
                            // 仅当终端设备被分配了APPSKEY的情况下被提供
        data?    : string;  // 数据包有效负载数据
                            // 仅当终端设备没有被分配APPSKEY的情况下被提供
        // 拓展的无线射频参数
        freq     : number;  // 无线频率
        dr       : string;  // 无线数据速率 - 包括扩频因子、带宽和码率
                            // e.g. SF12 BW125 4/5
        rssi     : number;  // 无线接收信号强度
        snr      : number;  // 无线信号信噪比
    }



#### Event: 'tx' 

    描述：用户通过此命令，可以向终端发送下行数据
    方向: 客户端到服务器(发送明文)
    数据格式:
    {
        cmd      : 'tx';	// 数据包的类型标识, tx = 下行数据
        EUI      : string;  // 设备EUI, 16位十六进制数(不包括横杠)
        port     : number;  // 向设备发下行数据使用的端口，范围是1至223
        data     : string;  // 数据包有效负载数据 (服务器将对其进行加密)
                            // 如果终端设备没有被分配APPSKEY，服务器将返回一个错误
        rx_window?: number; // 选择接收窗口（包括接收窗口1和接收窗口2），如果没有提供此项，服务器将使用默认的接收窗口
                            // A级设备默认接收窗口为1，C级为2 
        confirmed? : Bool;  // 若此项为True，此下行数据将是一个Confirmed Message，
                            // 即此下行数据下发后，服务器会等待终端设备回一个ack=1的数据包，否则将重发此下行数据至收到ack为止
    }
 
    方向: 客户端到服务器(发送密文)
    数据格式:
    {
        cmd      : 'tx';	// 数据包的类型标识, tx = 下行数据
        EUI      : string;  // 设备EUI，16位十六进制数(不包括横杠)
        port     : number;  // 向设备发下行数据使用的端口，范围是1至223
        seqno    : seqno;   // 此下行数据的序列号；
                            // seqno = fcnt + len(queue)；queue为数据队列，
                            // 如果序列号不同步，服务器将返回错误和同步的序列号。
        encdata  : string;  // 数据包有效负载数据 (已经用APPSKEY加密过)
                            // 负载数据必须用最新的序列号加密
        rx_window?: number; // 选择接收窗口（包括接收窗口1和接收窗口2），如果没有提供此项，服务器将使用默认的接收窗口
                            // A级设备默认接收窗口为1，C级为2 
        confirmed? : Bool;  // 若此项为True，此下行数据将是一个Confirmed Message，
                            // 即此下行数据下发后，服务器会等待终端设备回一个ack=1的数据包，否则将重发此下行数据至收到ack为止
    }

    方向: 客户端到服务器(发送组播数据明文到一个组播组中的所有设备)
    数据格式:
    {
        cmd      : 'mtx';	// 数据包的类型标识, mtx = 组播下行数据
        EUI      : string;  // 组播组EUI，16位十六进制数(不包括横杠)
        port     : number;  // 向设备发下行数据使用的端口，范围是1至223
        data     : string;  // 数据包有效负载数据 (服务器将对其进行加密)
                            // 如果终端设备没有被分配APPSKEY，服务器将返回一个错误
    }

    方向: 客户端到服务器(发送组播数据密文到一个组播组中的所有设备)
    数据格式:
    {
        cmd      : 'mtx';	// 数据包的类型标识, mtx = 组播下行数据
        EUI      : string;  // 组播组EUI，16位十六进制数(不包括横杠)
        port     : number;  // 向设备发下行数据使用的端口，范围是1至223
        seqno    : seqno;   // 此下行数据的序列号；
                            // seqno = fcnt + len(queue)；queue为数据队列，
                            // 如果序列号不同步，服务器将返回错误和同步的序列号。
        encdata  : string;  // 数据包有效负载数据 (已经用APPSKEY加密过)
                            // 负载数据必须用最新的序列号加密
    }


#### Event: 'ack_tx'
    方向: 服务器到客户端
    描述: 用户发送请求的确认信息,用户收到此信息说明下行数据已被加入发送队列，等待发送
    数据格式:
    {
        cmd      : 'tx' or 'mtx';	// 数据包的类型标识，tx = 单播下行数据，mtx = 组播下行数据
        EUI      : string;          // 设备EUI，16位十六进制数(不包括横杠)
        success? : Bool;            // 若命令成功执行，此项将为True
        error?   : string;          // 服务器返回的错误信息，此项仅命令执行失败时被提供
        data?    : string;          // 被放入数据队列的下行数据包 (无论是明文或是密文)
                                    // 此项仅命令执行成功时被提供
    }


#### Event: 'confirm_tx'
    方向: 服务器到客户端
    描述: 下行数据被下发至基站的确认信息，用户收到此信息说明下行数据已被下发至基站，基站将转发至终端设备
    数据格式:
    {
        cmd      : 'txd' or 'mtxd';	// 数据包的类型标识，tx = 单播下行数据，mtx = 组播下行数据
        EUI      : string;          // 设备EUI，16位十六进制数(不包括横杠)
        fcnt    : number;           // 下行数据的序列号
        ts       : number;          // 下发下行数据到基站时的时间戳
    }


#### Event: 'cache_query'
    方向: 客户端到服务器
    描述: 用户可通过此命令获取缓存在服务器的上行数据
    数据格式:
    {
        cmd      : 'cache_query';	    // 数据包的类型标识, cq = 获取缓存上行数据
        filter?   : {                   // 用户指定的限制参数
            start_ts?   : number;       // 指定开始时间戳，服务器将返回该时间以后的缓存上行数据
                                        // 默认为0
            end_ts?     : number;       // 指定结束时间戳，服务器将返回该时间以前的缓存上行数据
                                        // 默认为当前时间
            dev_eui?    : string;       // 指定获取特定设备的上行数据，默认为所有设备
            app_eui?    : string;       // 指定获取特定应用的上行数据，默认为说有应用
        },
        page_num? : number;              // 设置分页数，默认为1，即一页
        per_page? : number;              // 设置每页包含条目的数量，默认为100
    }

    方向: 服务器到客户端
    描述: 返回用户获取的缓存数据给用户
    数据格式:
    {
        cmd      : 'cache_query';	    // 数据包的类型标识, cq = 获取缓存上行数据
        filter?   : {                   // 返回用户指定的限制参数
            start_ts?   : number;
            end_ts?     : number;
            dev_eui?    : string;
            app_eui?    : string;
        },
        page_num : number;              // 返回用户指定的分页数
        per_page : number;              // 返回用户指定的每页包含条数数量
        total    : number;              // 在服务器缓存中，符合用户指定限制参数的上行数据数量
        cache    : list;                // 上行数据列表
    }