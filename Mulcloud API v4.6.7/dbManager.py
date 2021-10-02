from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///database.db', echo = False)
Base = declarative_base()

class User_Data(Base):
    __tablename__ = 'User_Data'
    id = Column(Integer, primary_key = True, autoincrement=True)
    email = Column(String, unique = True)
    password = Column(String)
    data = Column(String)
    cookies = Column(String)
    drive_data = Column(String)

class Defaults(Base):
    __tablename__ =  'Defaults'
    id = Column(Integer, primary_key = True)
    value = Column(Integer)


Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind = engine)
session = Session()

def insert_record(record):
    if not isinstance(record, list):
        record = [record]
    session.add_all(record)
    session.commit()


def query(cls, filter = None, first = True):
    if filter:
        res = session.query(cls).filter_by(**filter)
    else:
        res =  session.query(cls).all()
    if filter and first:
        res = res.first()
    return res, session

def delete_record(cls, filter = None):
    if filter:
        query = session.query(cls).filter_by(**filter).delete()
    else:
        query = session.query(cls).all().delete()
    session.commit()
