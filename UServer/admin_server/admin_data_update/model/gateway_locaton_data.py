# _*_ coding:utf-8 _*_
from database.db4 import db4, Channel4, ConstDB4
from utils.log import Logger, Action


class Location:

    channel_name = Channel4.gis_gateway_location + '*'

    def __init__(self):
        self.ps = db4.pubsub()

    def psubscribe_gis(self):
        self.ps.psubscribe(self.channel_name)
        return self.ps

    def stop_listen(self):
        if hasattr(self, 'ps'):
            self.ps.punsubscribe()

    def listen_gis_gateway_location(self):
        Logger.info(Action.listen, 'psubscribe', self.channel_name, 'Begin listen')
        ps_init = self.psubscribe_gis()
        for item in ps_init.listen():
            if item is not None:
                if item['type'] == 'pmessage':
                    Logger.info(Action.listen, item['channel'].decode(), 'MESSAGE', item['data'].decode())
                    gateway_id = item['channel'].decode().split(':')[1]

                    location_data = item['data'].decode().split(',')
                    if len(location_data) == 3:
                        lng = float(location_data[0])
                        lat = float(location_data[1])
                        alt = int(location_data[2])
                        msg = self.Object(gateway_id, lat=lat, lng=lng, alt=alt)
                        yield msg
                else:
                    Logger.info(Action.listen, item['channel'].decode(), item['type'], item['data'])

    class Object:
        def __init__(self, gw_id, lat, lng, alt):
            self.gateway_id = gw_id
            self.latitude = lat
            self.longitude = lng
            self.altitude = alt

