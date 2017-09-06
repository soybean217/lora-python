from sqlalchemy import Column, Integer, String, ForeignKey, Table, MetaData, and_, or_
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, sessionmaker, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI

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
