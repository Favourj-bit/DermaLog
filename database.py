from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy.orm import registry

mapper_registry = registry()
Base = mapper_registry.generate_base()

class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    skin_shade = Column(String)
    tone_range = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String)
    uploaded_image_path = Column(String)
    skin_color_image_path = Column(String)


# Replace 'myapp.db' with the path to the database file you want to use
# engine = create_engine('sqlite:////Users/favourjames/Downloads/DATA SCIENCE AND MACHINE LEARNING/robomua/myapp.db')
engine = create_engine('sqlite:///myapp.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


