from sqlalchemy import create_engine, Column, Integer, String, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///claims.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Claim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    policy_no = Column(String)
    name = Column(String)
    email = Column(String)
    date_of_loss = Column(Date)
    location = Column(String)
    damage_info = Column(JSON)
    weather_ok = Column(Integer)
    approved = Column(Integer)
    notes = Column(String)
    refund_tx = Column(String)

Base.metadata.create_all(engine)
