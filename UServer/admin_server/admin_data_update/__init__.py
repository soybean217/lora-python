# _*_coding: utf-8 _*_
from admin_server.admin_data_update.model.gateway_locaton_data import Location
from admin_server.admin_data_update.object.gateway import GatewayLocation
from admin_server.admin_data_update.model.gps import GPS


def main():
    location = Location()
    for data in location.listen_gis_gateway_location():
        data.latitude, data.longitude = GPS.wsg2gcj(data.latitude, data.longitude)
        history_data = GatewayLocation.query_gateway_id(data.gateway_id)
        if history_data is not None:
            check_result = GPS.check_gps_change_large(data.latitude, data.longitude,
                                                      history_data.latitude, history_data.longitude)
        else:
            # first time to get the gateway_id
            check_result = True
        if check_result:
            request = GPS.CODE(data.latitude, data.longitude)
            code = request.get(data.gateway_id)
            if code is not None:
                code_province = code[:2]
                code_city = code[2:4]
                code_area = code[4:6]
            else:
                code_province = ''
                code_city = ''
                code_area = ''
        else:
            # Do not need to get new code, just use the last code
            code_province = history_data.code_province
            code_city = history_data.code_city
            code_area = history_data.code_area

        if history_data is not None:
            GatewayLocation.update(id=history_data.id, gateway_id=data.gateway_id,
                                   latitude=data.latitude, longitude=data.longitude,
                                   altitude=data.altitude,
                                   code_province=code_province, code_city=code_city,
                                   code_area=code_area)
        else:
            GatewayLocation.insert(gateway_id=data.gateway_id,
                                   latitude=data.latitude, longitude=data.longitude,
                                   altitude=data.altitude,
                                   code_province=code_province, code_city=code_city,
                                   code_area=code_area)
