# _*_coding: utf-8 _*_
# from sqlalchemy import Column, String, INT, MetaData
# from admin_server.admin_data_update.object import Base, DBSession, engine, metadata

from sqlalchemy import Column, String, INT, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import SQLALCHEMY_BINDS
from utils.errors import KeyDuplicateError, ReadOnlyDeny
from .switch import SwitchType


Base = declarative_base()
engine = create_engine(SQLALCHEMY_BINDS['lorawan'], pool_recycle=3600)
conn = engine.connect()
metadata = MetaData()
DBSession = sessionmaker(bind=engine)


class Fields:
    ID = 'id'
    GATEWAY = 'gateway_id'
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    ALTITUDE = 'altitude'
    CODE_PROVINCE = 'code_province'
    CODE_CITY = 'code_city'
    CODE_AREA = 'code_area'


class GatewayLocation(Base):

    __tablename__ = 'lorawan_gateway_location'

    __input_switcher = {
        Fields.LATITUDE: SwitchType.float2string,
        Fields.LONGITUDE: SwitchType.float2string,
        Fields.ALTITUDE: SwitchType.int2string,
    }

    id = Column(INT, autoincrement=True, unique=True, nullable=False, primary_key=True)
    gateway_id = Column(String(16), unique=True, nullable=False)
    latitude = Column(String(11), default='0.0', nullable=False)
    longitude = Column(String(11), default='0.0', nullable=False)
    altitude = Column(String(5), default='0', nullable=False)
    code_province = Column(String(2), nullable=True)
    code_city = Column(String(2), nullable=True)
    code_area = Column(String(2), nullable=True)

    def __setattr__(self, key, value):
        # if hasattr(self, key):
        if self.__input_switcher.get(key):
            value = self.__input_switcher[key](value)
        super.__setattr__(self, key, value)

    def obj_to_dict(self):
        return {
            Fields.GATEWAY: self.gateway_id,
            Fields.LATITUDE: self.latitude,
            Fields.LONGITUDE: self.longitude,
            Fields.ALTITUDE: self.altitude,
            Fields.CODE_PROVINCE: self.code_province,
            Fields.CODE_CITY: self.code_city,
            Fields.CODE_AREA: self.code_area
        }

    class Object:

        __output_switcher = {
            Fields.LATITUDE: SwitchType.string2float,
            Fields.LONGITUDE: SwitchType.string2float,
            Fields.ALTITUDE: SwitchType.string2int,
        }

        def __init__(self, id, gateway_id, latitude, longitude, altitude, code_province, code_city, code_area):
            self.id = id
            self.gateway_id = gateway_id
            self.latitude = latitude
            self.longitude = longitude
            self.altitude = altitude
            self.code_province = code_province
            self.code_city = code_city
            self.code_area = code_area

        def __setattr__(self, key, value):
            if hasattr(self, key):
                raise ReadOnlyDeny
            if self.__output_switcher.get(key):
                value = self.__output_switcher[key](value)
            self.__dict__[key] = value

    @staticmethod
    def query_gateway_id(gateway_id):
        dbsession = DBSession()
        data = dbsession.query(GatewayLocation).filter(GatewayLocation.gateway_id == gateway_id).first()
        dbsession.close()
        if data:
            data = GatewayLocation.Object(id=data.id, gateway_id=data.gateway_id, latitude=data.latitude,
                                          longitude=data.longitude, altitude=data.altitude,
                                          code_province=data.code_province, code_city=data.code_city,
                                          code_area=data.code_area)
        else:
            data = None
        return data

    @staticmethod
    def query_code(code_province, code_city=None, code_area=None):
        dbsession = DBSession()
        query = dbsession.query(GatewayLocation).filter(GatewayLocation.code_province == code_province)
        if code_city is not None:
            query = query.filter(GatewayLocation.code_city == code_city)
            if code_area is not None:
                query = query.filter(GatewayLocation.code_area == code_area)
        data = query.all()
        if data:
            data = [
                GatewayLocation.Object(id=i_data.id, gateway_id=i_data.gateway_id, latitude=i_data.latitude,
                                       longitude=i_data.longitude, altitude=i_data.altitude,
                                       code_province=i_data.code_province, code_city=i_data.code_city,
                                       code_area=i_data.code_area) for i_data in data
                ]
        else:
            data = []
        return data

    @staticmethod
    def update(id, gateway_id, latitude, longitude, altitude, code_province, code_city, code_area):
        new_object = GatewayLocation(id=id, gateway_id=gateway_id, latitude=latitude, longitude=longitude, altitude=altitude,
                                     code_province=code_province, code_city=code_city, code_area=code_area)
        new_dict = new_object.obj_to_dict()
        dbsession = DBSession()
        dbsession.query(GatewayLocation).filter(GatewayLocation.id == id).update(new_dict)
        dbsession.commit()
        dbsession.close()

    @staticmethod
    def insert(gateway_id, latitude, longitude, altitude, code_province=None, code_city=None, code_area=None):
        dbsession = DBSession()
        gateway_init = GatewayLocation(gateway_id=gateway_id, latitude=latitude, longitude=longitude, altitude=altitude,
                                       code_province=code_province, code_city=code_city, code_area=code_area)
        dbsession.add(gateway_init)
        dbsession.commit()
        dbsession.close()


def create_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


if __name__ == '__main__':
    # create_db()
    from database.db0 import db0, ConstDB
    key_list = db0.keys(pattern=ConstDB.gateway + '*')
    for i_key in key_list:
        gateway_id = i_key.decode().split(':')[1]
        location = db0.hget(i_key, 'location')
        data = location.decode().split(',')
        lng = float(data[0])
        lat = float(data[1])
        alt = int(data[2])
        # print('id=%s lat=%s lng=%s' % (gateway_id, str(lat), str(lng)))
        GatewayLocation.insert(gateway_id=gateway_id, latitude=lat, longitude=lng, altitude=alt)

