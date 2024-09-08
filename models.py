'''
Модуль описания моделей таблиц базы данных.

'''
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from extrapacks.config import DB_DRIVER, DB_LOGIN, DB_PASSWORD, DB_CONNECTION, DB_PORT, DB_NAME


class DatabaseConfig:
    '''Класс подготовки базы данных к работе.

    '''
    Base = declarative_base()
    DSN = f'{DB_DRIVER}://{DB_LOGIN}:{DB_PASSWORD}@{DB_CONNECTION}:{DB_PORT}/{DB_NAME}'
    engine = sq.create_engine(DSN)
    Session = sessionmaker(engine)

    @classmethod
    def create_table(cls):
        '''Функция создания таблиц, по описанным моделям.

        '''
        cls.Base.metadata.create_all(cls.engine)

    @classmethod
    def delete_table(cls):
        '''Функция удаления всех созданных таблиц.

        '''
        cls.Base.metadata.drop_all(cls.engine)

    @classmethod
    def filling_out_gender(cls):
        '''Функция заполнения таблицы "gender".

           Заполнение осуществляется из файла data/names.txt.
        
        '''
        with cls.Session() as session:
            with open('data/names.txt', encoding='utf-8') as fr:
                for line in fr:
                    name, sex = line.rstrip().split('-')
                    model = Genders(name=name, sex=sex)
                    session.add(model)
            session.commit()


class Users(DatabaseConfig.Base):
    '''Модель таблицы "users".
       
       Хранит информацию о профилях пользователей.
       По принципу многие ко многим связана с таблицей "partners" (через таблицу "users_partners").

    '''
    __tablename__ = 'users'

    id_user = sq.Column(sq.BigInteger, primary_key=True)
    id_city = sq.Column(sq.Integer, nullable=False)
    age = sq.Column(sq.SmallInteger, nullable=False)
    sex = sq.Column(sq.SmallInteger, sq.CheckConstraint("sex = 1 or sex = 2", name='check_sex'))

    users_partners = relationship('UsersPartners', back_populates='users', cascade='all, delete-orphan')


class Partners(DatabaseConfig.Base):
    '''Модель таблицы "partners".
       
       Хранит информацию о партнерах.
       По принципу многие ко многим связана с таблицей "users" (через таблицу "users_partners").

    '''
    __tablename__ = 'partners'

    id_partner = sq.Column(sq.BigInteger, primary_key=True)
    first_name = sq.Column(sq.String(length=30), nullable=False)
    last_name = sq.Column(sq.String(length=30), nullable=False)
    link = sq.Column(sq.Text, nullable=False)

    users_partners = relationship('UsersPartners', back_populates='partners', cascade='all, delete-orphan')


class UsersPartners(DatabaseConfig.Base):
    '''Модель таблицы "users_partners".
       
       Связующая таблица между "users" и "partners".

    '''
    __tablename__ = 'users_partners'

    id_user = sq.Column(sq.BigInteger, sq.ForeignKey(Users.id_user))
    id_partner = sq.Column(sq.BigInteger, sq.ForeignKey(Partners.id_partner))
    ignore = sq.Column(sq.Boolean, default=False)
    sq.PrimaryKeyConstraint(id_user, id_partner)

    partners = relationship('Partners', back_populates='users_partners')
    users = relationship('Users', back_populates='users_partners')


class Genders(DatabaseConfig.Base):
    '''Модель таблицы "genders".
    
       Хранит информацию о соответствии имени полу.

    '''
    __tablename__ = 'genders'

    name = sq.Column(sq.String(length=30), primary_key=True)
    sex = sq.Column(sq.SmallInteger, sq.CheckConstraint("sex = 1 or sex = 2", name='check_sex'))


# if __name__ == '__main__':
#     DatabaseConfig.delete_table()
#     DatabaseConfig.create_table()
#     DatabaseConfig.filling_out_gender()
