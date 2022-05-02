from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Timers(Base):
    __tablename__ = "Timers"
    id = Column(Integer, primary_key=True)
    type = Column("Type", String)
    comment = Column("Comment", String)
    last_clicked = Column("Last_Clicked", Integer)
    data = Column("Data", String)

    def __init__(self, type, comment, last_clicked, data):
        self.type = type
        self.comment = comment
        self.last_clicked = last_clicked
        self.data = data


class Settings(Base):
    __tablename__ = "Settings"
    name = Column("Name", String, primary_key=True)
    value = Column("Value", Boolean)

    def __init__(self, name, value):
        self.name = name
        self.value = value


def initialize_db():
    engine = create_engine("sqlite:///timers.db")
    Base.metadata.create_all(engine)
    return engine
