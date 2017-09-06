# _*_ coding:utf-8 _*_
import eviltransform
import requests
from utils.log import Logger, Action


class GPS:
    LIMIT_DISTANCE = 10  # meter

    @staticmethod
    def check_gps_change_large(latitude_1, longitude_1, latitude_2, longitude_2):
        distance = GPS.compute_distance(latitude_1, longitude_1, latitude_2, longitude_2)
        if distance > GPS.LIMIT_DISTANCE:
            return True
        else:
            return False

    @staticmethod
    def compute_distance(latitude_1, longitude_1, latitude_2, longitude_2):
        # the unit of distance is meter.
        distance = eviltransform.distance(latitude_1, longitude_1,
                                          latitude_2, longitude_2)
        return int(distance)

    @staticmethod
    def wsg2gcj(latitude, longitude):
        gcj_lat, gcj_lng = eviltransform.wgs2gcj(latitude, longitude)
        return gcj_lat, gcj_lng

    class Object:
        def __init__(self, lat, lng, alt):
            self.latitude = lat
            self.longitude = lng
            self.altitude = alt

    class CODE:

        REQUEST_URL = 'http://restapi.amap.com/v3/geocode/regeo'
        REQUEST_KEY = '949a50bd9b5a7d8eaf6986c2bf1ea324'
        # REQUEST_KEY = 'b1b2409a9442b5091793be7336cc940c'
        TIMEOUT = 2

        def __init__(self, latitude, longitude):
            self.latitude = latitude
            self.longitude = longitude
            self.location_param = '%.6f,%.6f' % (self.longitude, self.latitude)

        def get(self, gateway_id):
            reslut = None
            payload = {'key': self.REQUEST_KEY, 'location': self.location_param, 'output': 'JSON'}
            try:
                response = requests.get(self.REQUEST_URL, params=payload, timeout=self.TIMEOUT)
                if response.status_code == requests.codes.ok:
                    response_data = response.json()
                    if response_data['status'] == '1':
                        self.normal_req(response_data, gateway_id)
                        code = response_data['regeocode']['addressComponent']['adcode']
                        reslut = code
                    else:
                        self.abnormal_req(response_data, gateway_id)
                else:
                    Logger.warning(Action.get, 'Code API', response.status_code, response.content)
            except requests.exceptions.Timeout as e:
                Logger.error(Action.get, 'Code API', '','ERROR: %s' % str(e))
            # except ValueError as e:
            #     print('ERROR: %s' % str(e))
            finally:
                return reslut

        def normal_req(self, response_data, gateway_id):
            Logger.info(Action.get, 'Code API', response_data['infocode'],
                        'id=%s location=%s' % (gateway_id, self.location_param))

        def abnormal_req(self, response_data, gateway_id):
            Logger.warning(Action.get, 'Code API', response_data['infocode'],
                           response_data['info'] + ' | id=%s location=%s' % (gateway_id, self.location_param))

if __name__ == '__main__':
    code_init = GPS.CODE(22.75306, 113.60394)
    code = code_init.get()
    print('code:', code)
