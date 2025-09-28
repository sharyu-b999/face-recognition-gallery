import pickle
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Person(Base):
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    photos = relationship('Photo', back_populates='person')

    @property
    def representative_photo(self):
        # If the person has photos, return the path of the first one; otherwise, return a default placeholder image
        if self.photos:
            return self.photos[0].path
        return 'default.png'  # Ensure this default image is placed in the `static/uploads` folder

class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    path = Column(String)
    person_id = Column(Integer, ForeignKey('persons.id'))
    person = relationship('Person', back_populates='photos')
    encoding = Column(PickleType)  # Ensure encoding is stored as PickleType for binary data

# Database setup
engine = create_engine('sqlite:///gallery.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
