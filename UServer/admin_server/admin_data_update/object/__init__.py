# from sqlalchemy import Column, String, INT, MetaData
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine
# from config import SQLALCHEMY_BINDS
#
# Base = declarative_base()
# engine = create_engine(SQLALCHEMY_BINDS['lorawan'], pool_recycle=3600)
# conn = engine.connect()
# metadata = MetaData()
#
# DBSession = sessionmaker(bind=engine)
