'''
Модуль тестирования класса Database модуля main.
По окончании тестирования удаляет все данные из таблиц "users", "partners", "users_partners".

'''
import sys
import os
sys.path.append(os.getcwd())

import pytest
import sqlalchemy as sq

from main import Database
from models import Genders, Users, Partners, UsersPartners, DatabaseConfig


@pytest.fixture(scope='function')
def filling_genders():
    '''Фикстура заполнения таблицы "genders" данными.
    '''
    try:
        DatabaseConfig.filling_out_gender()
    except sq.exc.IntegrityError:
        pass

@pytest.fixture(scope='module')
def delete_data():
    '''Фикстура удаления данных из таблиц "users", "partners", "users_partners".
    '''
    yield
    for table in (UsersPartners, Partners, Users):
        Database.session.query(table).delete()
    Database.session.commit()


@pytest.mark.parametrize(
    'name, result_manual',
    [('Aleksei', None),
     ('МаРИна', 1),
     ('анатолий', 2),
     ('ВикТор', 2),
     ('Алёна', 1)]
)
def test_get_gender(filling_genders, delete_data, name, result_manual):
    '''Тест функции get_gender.
    '''
    result_func = Database.get_gender(name)

    assert result_func == result_manual


@pytest.mark.parametrize(
        'user_info',
        [{'id_user': 123456789, 'id_city': 2, 'age': 20, 'sex': 2},
         {'id_user': 987654321, 'id_city': 4, 'age': 30, 'sex': 1}]
)
def test_upload_user_info(user_info):
    '''Тест функции upload_user_info.
    '''
    Database.upload_user_info(user_info)
    result = Database.session.query(Users).\
        filter(Users.id_user == user_info['id_user']).scalar()
    result_func = {column: getattr(result, column) for column in result.__table__.c.keys()}

    assert result_func == user_info


def test_get_users():
    '''Тест функции get_users.
    '''
    result_func = Database.get_users()

    assert isinstance(result_func, dict)
    assert len(result_func) >= 2
    assert all(isinstance(value, dict) for value in result_func.values())


@pytest.mark.parametrize(
        'user_info',
        [{'id_user': 123456789, 'id_city': 2, 'age': 20, 'sex': 2},
         {'id_user': 987654321, 'id_city': 4, 'age': 30, 'sex': 1}]
)
def test_get_user_info(user_info):
    '''Тест функции get_user_info.
    '''
    result_func = Database.get_user_info(user_info['id_user'])

    assert isinstance(result_func, dict)
    assert len(result_func) == 4
    assert result_func == user_info

@pytest.mark.parametrize(
        'user_id',
        [123456789, 987654321]
)
@pytest.mark.parametrize(
        'partner_info',
        [{'id': 123123123, 'first_name': 'Алена', 'last_name': 'Тесты'},
         {'id': 456456456, 'first_name': 'Виктор', 'last_name': 'Тесты'}]
)
def test_upload_partner_info(user_id, partner_info):
    '''Тест функции upload_partner_info.
    '''
    Database.upload_partner_info(user_id, partner_info)

    partner_id = partner_info['id']
    partner_info_pattern ={
        'id_partner': partner_info['id'],
        'link': f'https://vk.com/id{partner_info['id']}',
        'first_name': partner_info['first_name'],
        'last_name': partner_info['last_name']
    }

    result = Database.session.query(Partners).\
        filter(Partners.id_partner == partner_info['id']).scalar()
    result_func = {column: getattr(result, column) for column in result.__table__.c.keys()}

    assert result_func == partner_info_pattern

    result = Database.session.query(UsersPartners).\
        filter(UsersPartners.id_partner == partner_id, 
               UsersPartners.id_user == user_id).scalar()
    
    assert result.id_user == user_id
    assert result.id_partner == partner_id


@pytest.mark.parametrize(
        'partner_id', [123123123, 456456456])
def test_check_prkey_in_partners(partner_id):
    '''Тест функции check_prkey_in_partners.
    '''
    result_func = Database.check_prkey_in_partners(partner_id)

    assert result_func is True


@pytest.mark.parametrize(
        'user_id', [123456789, 987654321])
@pytest.mark.parametrize(
        'partner_id', [123123123, 456456456])
def test_check_ignore(user_id, partner_id):
    '''Тест функции check_ignore.
    '''
    result_func = Database.check_ignore(user_id, partner_id)

    assert result_func is False


@pytest.mark.parametrize(
        'user_id', [123456789, 987654321])
@pytest.mark.parametrize(
        'partner_id', [123123123, 456456456])
def test_check_prkey_in_users_partners(user_id, partner_id):
    '''Тест функции check_prkey_in_users_partners.
    '''
    result_func = Database.check_prkey_in_users_partners(user_id, partner_id)
    
    assert result_func is True


@pytest.mark.parametrize(
        'user_id', [123456789, 987654321])
def test_get_favorite_partners(user_id):
    '''Тест функции get_favorite_partners.
    '''
    result_func = Database.get_favorite_partners(user_id)

    assert isinstance(result_func, list)
    assert len(result_func) == 2