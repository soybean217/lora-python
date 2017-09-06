from sqlalchemy import Column, String, BINARY, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


Base = declarative_base()


# class Application(Base):
#     __tablename__ = 'app'
#     app_eui = Column(BINARY(8), primary_key=True)
#     http_push = relationship('HttpPush',)


class HttpPush(Base):
    __tablename__ = 'http_push'

    app_eui = Column(BINARY(8), primary_key=True)
    url = Column(String(200), nullable=False)

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_recycle=3600)

sess = Session(engine)