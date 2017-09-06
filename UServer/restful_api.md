#  [LoRaWAN API](http://183.230.40.231:8108) - Http API Reference

## URL rule:

    '/login'    index for login page    (POST)
    
    '/apps' index for Application list  (GET, POST)
    '/apps/{app_eui}'   index for an Application    (GET, PATCH, DELETE)
    
    '/devices'  index for Device list   (GET, POST)
    '/devices/{dev_eui}'    index for an device (GET, PATCH, DELETE)
    
    '/groups'   index for Group list    (GET, POST)
    '/groups/{group_id}' index for an group (GET, PATCH, DELETE)
    
    '/gateways' index for Gateway list  (GET, POST)
    '/gateways/{gateway_id}'    index for a gataway (GET, PATCH, DELETE)
    
    '/msgs-up'  index of Message Up list    (GET)
    '/msgs-down'index of Message Down list  (GET)
   

# Login [/login]

Post user's account and get auth token. If you do not have a LoRaWAN account, you can register in our web server 'http://183.230.40.231:8008'.

## Post Account [POST]

+ Attributes
    + email     (string, required)
    + password  (string, required)
    
+ Request (application/json)

    + Body
    
            {
                "email"     :   string  ,
                "password"  :   string  ,
            }
          
+ Response 200 (application/json)
    
        {
            "auth_token"    :   string  ,
        }
        
# Applications [/apps]

Directory of applications posted by user.

## Retrieve Applications Resource [GET]

Retrieves the list of **Application** posts.

+ Request Retrieve all Applications
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 200 (application/json)

        [list of applications]
    
## Create a Application [POST]

Create a new **Application**

+ Attributes
    + app_eui   (string, required) - 16 hex digits
    + freq_plan (string, required) - Up to now only "EU863_870", "EU433" and "CN470_510" frequency plan is supported
    + name      (string, optional) - String

+ Request Create Application (application/json)
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

    + Body

            {
                "name"      :   str,
                "app_eui"   :   str,    //16 hex digits
                "freq_plan" :   str,    //??
            }

+ Response Give Back The Posted Resource 201 (application/json)
    
        Application Resource
        
+ Response 406 (application/json)

        {   
            "succeed"   :   False           ;
            "errors"    :   list of errors  ;
        } 
           
## Patch a Application [PATCH /apps/{app_eui}]

Edit Attributes of **Application**

+ Parameters
    + app_eui   (string)    -   EUI of Application   

+ Attributes
    + freq_plan (string, optional)  -   Up to now only "EU863_870", "EU433" and "CN470_510" frequency plan is supported
    + name      (string, optional)  -   String
    + token     (boolean, optional) -   generate new token if boolean is True
    
+ Request Patch Application (application/json)

        {
            "name"?     :   string  ,
            "freq_plan"?:   string  ,
            "token"?    :   boolean ,
        }

+ Response Give Back The Patched Resource 200 (application/json)
    
        Application Resource

## Delete a Application [DELETE /apps/{app_eui}]

Delete a **Application** posts

+ Parameters
    + app_eui   (string)    -   EUI of Application   
    
+ Request Delete Application
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 204
    
        {   
            "succeed"   :   True    ,
            "msg"       :   string  ,
        }
        
# Devices [/devices]
Directory of Devices posted by user.

## Retrieve Devices Resource [GET]

Retrieves the list of **Devices** posts.

+ Parameters
    + app_eui   (string, optional)  -   EUI of Application   
    + group_id  (string, optional)  -   
    
+ Request Retrieve all Devices
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 200 (application/json)

        [list of devices]
    
## Create a Device [POST]

Create a new **Device**

+ Attributes
    + name      (string, optional)  -   
    + dev_eui   (string, required)  -   EUI of Device, 16 hex digits
    + app_eui   (string, required)  -   EUI of Application, 16 hex digits
    + addr      (string, required)  -   Device address, 8 hex digits
    + nwkskey   (string, required)  -   Network session key of Device, 32 hex digits
    + appskey   (string, optional)  -   Application session key of Device, 32 hex digits

+ Request Create Device (application/json)
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

    + Body

            {
                "name"      :   string,
                "dev_eui"   :   string,   //16 hex digits
                "app_eui"   :   string,   //16 hex digits
                "addr"      :   string,   //8 hex digits
                "nwkskey"   :   string,   //32 hex digits
                "appskey"?  :   string,   //32 hex digits
            }

+ Response Give Back The Posted Resource 201 (application/json)
    
        Device Resource
        
+ Response 406 (application/json)

        {   
            "succeed"   :   False           ;
            "errors"    :   list of errors  ;
        } 
           
## Patch a Device [PATCH /devices/{dev_eui}]

Edit Attributes of **Application**

+ Parameters
    + dev_eui   (string)    -   EUI of Application   

+ Attributes 
    + name      (string, optional)  -
    + addr      (string, optional)  -   Device address, 8 hex digits
    + nwkskey   (string, optional)  -   Network session key of Device, 32 hex digits
    + appskey   (string, optional)  -   Application session key of Device, 32 hex digits
    + que_down  (boolean,optional)  -   Reset fcnt down
    + fcnt_down (number, optional)  -   
    + fcnt_up   (number, optional)  -   
    + dev_class (string, optional)  -   
    + adr       (boolean,optional)  -
    + check_fcnt(boolean,optional)  -   
    
+ Request Patch Device (application/json)

        {
            "name"?     :   string  ,
            "addr"?     :   string  ,
            "nwkskey"?  :   string  ,
            "appskey"?  :   string  ,
            "que_down"? :   
            "fcnt_down"?:   number  ,
            "fcnt_up"?  :   number  ,
            "dev_class"?:   string  ,
            "adr"?      :
            "check_fcnt"?:  
        }

+ Response Give Back The Patched Resource   200 (application/json)
    
        Device Resource

## Delete a Device [DELETE /devices/{dev_eui}]

Delete a **Device** posts

+ Parameters
    + dev_eui   (string)    -   EUI of Device   
    
+ Request Delete Device
    + Headers
    
            Authorization   :   Basic or Token
            Basic:  username=email password=password
            example:    "Basic {basic 64 string}"
                    Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 204
    
        {   
            "succeed"   :   True    ,
            "msg"       :   string  ,
        }
        
# Batch Manage Devices [/devices/batch]

## Get Batch Import Template [GET ]
        
# Groups [/devices]
Directory of **Groups** posted by user.

## Retrieve Groups Resource [GET]???

Retrieves the list of **Groups** posts.

+ Parameters
    + app       (string, optional)  -   EUI of Application   
    + group     (string, optional)  -   
    
+ Request Retrieve all Groups
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 200 (application/json)

        [list of groups]
    
## Create a Group [POST]

Create a new **Group**

+ Attributes
    + name      (string, optional)  -   
    + app_eui   (string, required)  -   EUI of Application, 16 hex digits
    + addr      (string, required)  -   Device address, 8 hex digits
    + nwkskey   (string, required)  -   Network session key of Device, 32 hex digits
    + appskey   (string, optional)  -   Application session key of Device, 32 hex digits

+ Request Create Group (application/json)
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

    + Body

            {
                "name"      :   string,
                "app_eui"   :   string,   //16 hex digits
                "addr"      :   string,   //8 hex digits
                "nwkskey"   :   string,   //32 hex digits
                "appskey"?  :   string,   //32 hex digits
            }

+ Response Give Back The Posted Resource 201 (application/json)
    
        Group Resource
        
+ Response 406 (application/json)

        {   
            "succeed"   :   False           ;
            "errors"    :   list of errors  ;
        } 
           
## Patch a Group [PATCH /groups/{group_id}]

Edit Attributes of **Group**

+ Parameters
    + group_id  (string)    -   ID of group 

+ Attributes 
    + name      (string, optional)  -
    + addr      (string, optional)  -   Device address, 8 hex digits
    + nwkskey   (string, optional)  -   Network session key of Group, 32 hex digits
    + appskey   (string, optional)  -   Application session key of Group, 32 hex digits
    + que_down  (boolean,optional)  -   Reset fcnt down
    + fcnt      (number, optional)  -   
    + periodicity(number,optional)  -   from 0 to 6 
    
+ Request Patch Group (application/json)

        {
            "name"?     :   string  ,
            "addr"?     :   string  ,
            "nwkskey"?  :   string  ,
            "appskey"?  :   string  ,
            "que_down"? :   boolean ,
            "fcnt"?     :   number  ,
            "periodicity"?: number  ,
        }
        
+ Response Give Back The Patched Resource   200 (application/json)
        
        Group Resource

## Delete a Group [DELETE /groups/{group_id}]

Delete a **Group**

+ Parameters
    + group_id  (string)    -   EUI of Device   
    
+ Request Delete Group
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 204
    
        {   
            "succeed"   :   True    ,
            "msg"       :   string  ,
        }
        
# Gateways [/gateways]
Directory of Gateways posted by user.

## Retrieve Gateways Resource [GET]

Retrieves the list of **Gateways** posts.
    
+ Request Retrieve all Gateways
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 200 (application/json)

        [list of Gateways]
    
## Create a Gateway [POST]

Create a new **Gateway**

+ Attributes
    + name      (string, optional)  -   
    + mac_addr  (string, required)  -   
    + platform  (string, required)  -   
    + latitude  (number, required)  -  
    + longitude (number, required)  -   
    + altitude  (number, required)  -   
    + model     (string, optional)  -
    + frequency (string, required)  -

+ Request Create Gateway (application/json)
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

    + Body

            {
                "name"      :   string  ,
                "mac_addr"  :   string  ,
                "platform"  :   string  ,
                "latitude"  :   number  ,
                "longitude" :   number  ,
                "altitude"  :   number  ,
                "frequency" :   string  ,
                "model"     :   string  ,
            }

+ Response Give Back The Posted Resource 201 (application/json)
    
        Gateway Resource 
        
+ Response 406 (application/json)

        {   
            "succeed"   :   False           ;
            "errors"    :   list of errors  ;
        } 
           
## Patch a Gateway [PATCH /gateways/{gateway_id}]

Edit Attributes of **Gateway**

+ Parameters
    + gateway_id(string)    -   ID of Gateway   

+ Attributes 
    + name      (string, optional)  -
    + frequency (string, optional)  -   
    + public    (boolean, optional) -   
    + disable   (boolean, optional) -   
    
+ Request Patch Gateway (application/json)

        {
            "name"?     :   string  ,
            "frequency"?:   string  ,
            "public"?   :   boolean ,
            "disable"?  :   boolean ,
        }
        
+ Response Give Back The Patched Resource 201 (application/json)
    
        Gateway Resource

## Delete a Gateway [DELETE /gateways/{gateway_id}]

Delete a **Gateway**

+ Parameters
    + gateway   (string)    -   ID of Gateway   
    
+ Request Delete Gateway
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 204
    
        {   
            "succeed"   :   True    ,
            "msg"       :   string  ,
        }
        
# Message Up [/msg-up]
Directory of Message Up.

## Retrieve Message Up [GET]

Retrieves the list of **Message Up**.

+ Parameters
    + app       (string, optional)  -   EUI of Application   
        + default   :   None    -   Retrieve message down of all Applications
    + device    (string, optional)  -   EUI of Device
    + start_ts  (number, optional)  -   Time stamp of the oldest msg down that user want to retrieve
        + default   :   0
    + end_ts    (number, optional)  -   Time stamp of the newest msg down that user want to retrieve
        + default   :   recent time stamp
        
+ Request Retrieve all Devices
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"

+ Response 200 (application/json)

        [list of Message Up]
        
# Message Down [/msg-down]
Directory of Message Down.

## Retrieve Message Down [GET]

Retrieves the list of **Message Down**.

+ Parameters
    + app       (string, optional)  -   EUI of Application
        + default   :   None    -   Retrieve message down of all Applications
    + device    (string, optional)  -   EUI of Device
    + group     (string, optional)  -   ID of Group
    + start_ts  (number, optional)  -   Time stamp of the oldest msg down that user want to retrieve
        + default   :   0
    + end_ts    (number, optional)  -   Time stamp of the newest msg down that user want to retrieve
        + default   :   recent time stamp
    
+ Request Retrieve all Devices
    + Headers
    
            Authorization   :   Basic or Token
                Basic:  username    :   emial
                        password    :   password
                    example:    "Basic {basic 64 string}"
                Token:  auth_token
                    example:    "Token {auth_token}"
                
+ Response 200 (application/json)

        [list of Message Down]