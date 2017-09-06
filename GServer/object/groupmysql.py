from sqlalchemy import Column, Integer, String, ForeignKey, Table, MetaData, and_, or_
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, sessionmaker, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI
from utils.db0 import db0, ConstDB0

Base = declarative_base()


class Group(Base):
    __tablename__ = 'group'

    id = Column(String(16), unique=True, nullable=False, primary_key=True)
    devs = relationship("Dev", secondary='group_dev')


class Dev(Base):
    __tablename__ = 'dev'

    id = Column(String(16), unique=True, nullable=False, primary_key=True)
    groups = relationship(Group, secondary='group_dev')


class GroupDevice(Base):
    __tablename__ = 'group_dev'
    group_id = Column(String(16), ForeignKey('group.id'), primary_key=True)
    dev_id = Column(String(16), ForeignKey('dev.id'), primary_key=True)
    extra_data = Column(String(50))
    group_a = relationship(Group, backref=backref("dev_assoc"))
    dev_a = relationship(Dev, backref=backref("group_assoc"))

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_recycle=3600)  # create connection pool
conn = engine.connect()
metadata = MetaData()
DBSession = sessionmaker(bind=engine)  # if set autocommit=True,it will auto invoke Session.query() or Session.execute()


def create_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


def insert_data():
    keys_list = db0.keys(pattern=ConstDB0.group_dev + '*')
    data = [i_key.decode() for i_key in keys_list]
    dbsession = DBSession()
    # data = ["DEV_GROUP:000080ca9f100d33:0102030405060709",
    #         "DEV_GROUP:003269cc62222aaf:be00000000000012",
    #         "DEV_GROUP:003269cc62222aaf:be00000000000010",
    #         "DEV_GROUP:003269cc62222aaf:be00000000000011",
    #         "DEV_GROUP:003473a9a476b712:0000000000000002",
    #         "DEV_GROUP:003473a9a476b712:0000000000000003",
    #         "DEV_GROUP:003269cc62222aaf:be00000000000013",
    #         "DEV_GROUP:000080ca9f100d33:3530353460358d0b",
    #         "DEV_GROUP:003473a9a476b712:0000000000000001"
    #         ]
    for i_data in data:
        group_id = i_data.split(':')[1]
        dev_id = i_data.split(':')[2]
        group_init = Group(id=group_id)
        dev_init = Dev(id=dev_id)
        query = dbsession.query(Group).filter(Group.id == group_id)
        if query.count() == 0:
            dbsession.add(group_init)
        else:
            group_init = query.first()
        query = dbsession.query(Dev).filter(Dev.id == dev_id).count()
        if query == 0:
            dbsession.add(dev_init)
        # dbsession.commit()
        query = dbsession.query(GroupDevice).filter(and_(GroupDevice.dev_id == dev_id,
                                                         GroupDevice.group_id == group_id)).count()
        if query == 0:
            group_init.devs.append(dev_init)
        dbsession.commit()
    dbsession.close()


def query_data():
    group_id = '003269cc62222aaf'
    dbsession = DBSession()
    query = dbsession.query(GroupDevice.dev_id).filter(GroupDevice.group_id == group_id).all()
    data = [i_query[0] for i_query in query]
    print('query:', data)


if __name__ == '__main__':
    create_db()
    # drop_db()
    # insert_data()
    # query_data()
    dbsession = DBSession()
    data = ["DEV_GROUP:000080ca9f100d30:0102030405060708"]
    for i_data in data:
        group_id = i_data.split(':')[1]
        dev_id = i_data.split(':')[2]
        group_init = Group(id=group_id)
        dev_init = Dev(id=dev_id)

        query = dbsession.query(GroupDevice).filter(and_(GroupDevice.dev_id == dev_id,
                                                         GroupDevice.group_id == group_id))
        if query.count() != 0:
            for i_query in query.all():
                dbsession.delete(i_query)
        # query = dbsession.query(Dev).filter(Dev.id == dev_id)
        # dbsession.delete(query.first())
    dbsession.commit()
    dbsession.close()



