from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_test_engine():
    return create_engine('sqlite:///:memory:')

def get_test_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

