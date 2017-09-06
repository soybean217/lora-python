##  [LoRaWAN](http://183.230.40.231:8108) - Http API Reference

URL rule:

    '/api/v1/apps' all apps for user
    '/api/v1/apps/<app_eui>' index for an application
    
    '/api/v1/devices' all devices for user
        '/api/v1/devices?app_eui=xxxxxxxxxxxxxxxx' all devices of application
    '/api/v1/devices/<dev_eui>' index for an device
    
    '/api/v1/groups' all groups for user
        '/api/v1/groups?app_eui=xxxxxxxxxxxxxxxx' get all groups of application
        '/api/v1/groups?app_eui=xxxxxxxxxxxxxxxx&group_id=xxxxxxxx' one group of application
    '/api/v1/groups/<app_eui>/<group_id_>' index for an group
    
    
    '/api/v1/msgs-up' all msgs up for user
    
    
    
    '/api/v1/groups/msg'
    '/api/v1/groups/msg?filter'
    
    'gateways?filter'
    
    
    edit group
    {
        'name'? : str,
        'addr'? : str,  //8 hex
        'nwkskey'? : str,   //32 hex
        'appskey'? : str,   //32 hex
        'rm_appskey': boolean,
        'reset_fcnt_down'?: boolean,
        'reset_fcnt_up'? : boolean,
        'periodicity'?: int (from 0 to 6),
        'datr'? : int (from 0 to 6),
        'add_dev'?  : str(dev_eui),   //16 hex
        'rm_dev'?   : str(dev_eui),   //16 hex
    }
    
    edit device
    {
        'addr'? : str,
        'name'? : str,
        'nwkskey'?:str,
        'appskey'?:str,
        'rm_appskey'?:boolean,
        'reset_fcnt_down'?: boolean,
        'reset_fcnt_up'? : boolean,
        'dev_class'?: str (A or C),
        'adr'?: boolean,
        'check_fcnt'?:  boolean,    //(1: strict, 2: relaxed)
    }
    
    
    
    