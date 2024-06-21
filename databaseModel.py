from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

# SQLAlchemy setup
engine = create_engine('sqlite:///todo_database.db')  # Adjust path as needed
Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_current_ist_time():
    tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(tz)

# Define ORM classes
class Country(Base):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    states = relationship('State', back_populates='country')

    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __repr__(self):
        return f"Country(id={self.id}, name='{self.name}', code='{self.code}')"

class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    country_id = Column(Integer, ForeignKey('country.id'), nullable=False)
    country = relationship('Country', back_populates='states')

    def __init__(self, name, country):
        self.name = name
        self.country = country

    def __repr__(self):
        return f"State(id={self.id}, name='{self.name}', country_id={self.country_id})"

class Gender(Base):
    __tablename__ = 'gender'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Gender(id={self.id}, name='{self.name}')"

class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(255))
    state_id = Column(Integer, ForeignKey('state.id'))
    city = Column(String(100))
    pincode = Column(String(10))
    user_id = Column(Integer, ForeignKey('user.id'))

    user = relationship('User', back_populates='addresses')
    state = relationship('State')

    def __init__(self, address, state_id, city, pincode):
        self.address = address
        self.state_id = state_id
        self.city = city
        self.pincode = pincode

    def __repr__(self):
        return f"Address(id={self.id}, address='{self.address}', city='{self.city}', pincode='{self.pincode}')"

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50), unique=True)
    password = Column(String(12))
    username = Column(String(50), unique=True)
    phone = Column(String(15))
    gender_id = Column(Integer, ForeignKey('gender.id'))
    birthdate = Column(DateTime)
    profile_pic = Column(String(100))

    todos = relationship("Todolist", back_populates="user")
    addresses = relationship('Address', back_populates='user')
    history = relationship('UserHistory', back_populates='user')

    def __init__(self, first_name, last_name, email, password, username, phone, gender_id, birthdate, profile_pic):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.username = username
        self.phone = phone
        self.gender_id = gender_id
        self.birthdate = birthdate
        self.profile_pic = profile_pic

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"

class UserHistory(Base):
    __tablename__ = 'user_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50))
    password = Column(String(12))
    username = Column(String(50), unique=True)
    phone = Column(String(15))
    gender_id = Column(Integer, ForeignKey('gender.id'))
    birthdate = Column(DateTime)
    profile_pic = Column(String(100))
    created_at = Column(DateTime, default=get_current_ist_time)

    user = relationship('User', back_populates='history')
    gender = relationship('Gender')

    def __init__(self, user_id, first_name, last_name, email, password, username, phone, gender_id, birthdate, profile_pic):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.username = username
        self.phone = phone
        self.gender_id = gender_id
        self.birthdate = birthdate
        self.profile_pic = profile_pic

    def __repr__(self):
        return f"UserHistory(id={self.id}, username='{self.username}', email='{self.email}', created_at='{self.created_at}')"

class Todolist(Base):
    __tablename__ = 'todolist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    todo_title = Column(String(50), nullable=False)
    todo_desc = Column(String(1000))
    created_on = Column(DateTime)
    work_time = Column(Integer)
    iscompleted = Column(Boolean, default=False)
    completed_on = Column(DateTime, default=None)
    overdue = Column(String(30), default=None)

    user = relationship("User", back_populates="todos")

    def __init__(self, todo_title, todo_desc, created_on, work_time, user, iscompleted, completed_on, overdue):
        self.todo_title = todo_title
        self.todo_desc = todo_desc
        self.created_on = created_on
        self.work_time = work_time
        self.iscompleted = iscompleted
        self.completed_on = completed_on
        self.overdue = overdue
        self.user = user

    def __repr__(self):
        return f"Todolist(id={self.id}, title='{self.todo_title}', completed={self.iscompleted}, work_time={self.work_time}, completed_on='{self.completed_on}', overdue='{self.overdue}')"

# Create tables in the database
Base.metadata.create_all(engine)

# Function to initialize sample data
def initialize_sample_data():
    session = Session()
    try:
        # Populate gender data if not already populated
        if session.query(Gender).count() == 0:
            genders = [
                Gender(name='Male'),
                Gender(name='Female'),
                Gender(name='Other')
            ]
            session.add_all(genders)
            session.commit()

        # Populate country and state data if not already populated
        if session.query(Country).count() == 0:
            # Create India country
            india = Country(name='India', code='IN')
            session.add(india)
            session.commit()

            # Create states for India
            states = [
                State(name='Maharashtra', country=india),
                State(name='Delhi', country=india),
                State(name='Tamil Nadu', country=india),
                # Add more states as needed
            ]
            session.add_all(states)
            session.commit()

        # Check if users exist
        if session.query(User).count() == 0:
            # Fetch the Country object for India
            india = session.query(Country).filter_by(name='India').first()

            # Create User 1
            u1 = User(
                first_name='Omkar',
                last_name='Varma',
                email='omkar@email.com',
                password='omkar',
                username='omkarvarma',
                phone='1234567890',
                gender_id=1,  # Assuming 'Male' gender
                birthdate=datetime(1990, 1, 1),
                profile_pic='profile1.jpg',
            )
            u1.country = india  # Assign the Country object directly

            # Add User 1 history
            u1.history.append(UserHistory(
                first_name=u1.first_name,
                last_name=u1.last_name,
                email=u1.email,
                password=u1.password,
                username=u1.username,
                phone=u1.phone,
                gender_id=u1.gender_id,
                birthdate=u1.birthdate,
                profile_pic=u1.profile_pic,
            ))

            #
            # Create Address for User 1
            address1 = Address(
                address='123, ABC Road',
                state_id=session.query(State).filter_by(name='Maharashtra').first().id,
                city='Mumbai',
                pincode='400001'
            )
            u1.addresses.append(address1)

            # Create User 2
            u2 = User(
                first_name='Test1',
                last_name='User1',
                email='test1@email.com',
                password='test1',
                username='testuser1',
                phone='1234567891',
                gender_id=2,  # Assuming 'Female' gender
                birthdate=datetime(1991, 2, 2),
                profile_pic='profile2.jpg',
            )
            u2.country = india  # Assign the Country object directly

            # Add User 2 history
            u2.history.append(UserHistory(
                first_name=u2.first_name,
                last_name=u2.last_name,
                email=u2.email,
                password=u2.password,
                username=u2.username,
                phone=u2.phone,
                gender_id=u2.gender_id,
                birthdate=u2.birthdate,
                profile_pic=u2.profile_pic,
            ))

            # Create Address for User 2
            address2 = Address(
                address='456, XYZ Road',
                state_id=session.query(State).filter_by(name='Delhi').first().id,
                city='Delhi',
                pincode='110001'
            )
            u2.addresses.append(address2)

            # Add users to session and commit
            session.add_all([u1, u2])
            session.commit()

    except Exception as e:
        session.rollback()
        raise Exception(f"An error occurred: {str(e)}")
    finally:
        session.close()

# Call the function to initialize sample data
initialize_sample_data()
