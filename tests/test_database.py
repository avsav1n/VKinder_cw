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
from models import Users, Partners, UsersPartners, DatabaseConfig


class DataManager:
    '''Класс для обмена данными между тестовымы функциями и фикстурами.
    '''
    test_users_info = [
        {'id_user': 111111111, 'id_city': 2, 'sex': 1, 'age': 25},
        {'id_user': 333333333, 'id_city': 2, 'sex': 2, 'age': 30}
    ]
    test_partners_info = [
        {'id_partner': 222222222, 'first_name': 'Викатест',
         'last_name': 'Тест', 'link': 'https://vk.com/id222222222'},
        {'id_partner': 444444444, 'first_name': 'Мишатест',
         'last_name': 'Тест', 'link': 'https://vk.com/id444444444'}
    ]
    test_new_users = []
    test_new_partners = []

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DataManager, cls).__new__(cls)
        return cls.instance


@pytest.fixture(scope='function')
def filling_genders():
    '''Фикстура заполнения таблицы "genders" данными.
    '''
    try:
        DatabaseConfig.filling_out_gender()
    except sq.exc.IntegrityError:
        pass


@pytest.fixture(scope='module', autouse=True)
def filling_delete_test_data():
    '''Фикстура добавления и удаления тестовых данных.
    '''
    tsession = DatabaseConfig.Session()
    manager = DataManager()

    for user in manager.test_users_info:
        model = Users(**user)
        tsession.add(model)
    for index, partner in enumerate(manager.test_partners_info):
        model = Partners(**partner)
        association_data = UsersPartners(id_user=manager.test_users_info[0]['id_user'],
                                         ignore=bool(index))
        model.users_partners = [association_data]
        tsession.add(model)
    tsession.commit()

    yield

    manager.test_users_info.extend(manager.test_new_users)
    manager.test_partners_info.extend(manager.test_new_partners)

    for user_id in {user['id_user'] for user in manager.test_users_info}:
        test_user = tsession.query(Users).filter(Users.id_user == user_id).one()
        tsession.delete(test_user)
    tsession.commit()

    for partner_id in {partner['id_partner'] for partner in manager.test_partners_info}:
        test_partner = tsession.query(Partners).filter(Partners.id_partner == partner_id).one()
        tsession.delete(test_partner)
    tsession.commit()

    tsession.close_all()


@pytest.mark.parametrize('name, result_manual',
    [('Aleksei', None),
     ('МаРИна', 1),
     ('анатолий', 2),
     ('ВикТор', 2),
     ('Алёна', 1)])
def test_get_gender(filling_genders, name, result_manual):
    '''Тест функции get_gender.
    '''
    result_func = Database.get_gender(name)
    assert result_func == result_manual


@pytest.mark.parametrize('user_info',
    [{'id_user': 555555555, 'id_city': 1, 'age': 20, 'sex': 2},
     {'id_user': 777777777, 'id_city': 1, 'age': 35, 'sex': 1}])
def test_upload_user_info(user_info):
    '''Тест функции upload_user_info.
    '''
    Database.upload_user_info(user_info)
    result = Database.session.query(Users).\
        filter(Users.id_user == user_info['id_user']).scalar()
    result_func = {column: getattr(result, column) for column in result.__table__.c.keys()}
    assert result_func == user_info

    DataManager.test_new_users.append(result_func)


def test_get_users():
    '''Тест функции get_users.
    '''
    result_func = Database.get_users()
    assert isinstance(result_func, dict)
    assert len(result_func) >= 2
    assert all(isinstance(value, dict) for value in result_func.values())


@pytest.mark.parametrize('user_info', DataManager.test_users_info)
def test_get_user_info(user_info):
    '''Тест функции get_user_info.
    '''
    result_func = Database.get_user_info(user_info['id_user'])
    assert isinstance(result_func, dict)
    assert len(result_func) == 4
    assert result_func == user_info


@pytest.mark.parametrize(
    'user_id',
    [info['id_user'] for info in DataManager.test_users_info])
@pytest.mark.parametrize(
    'partner_info',
    [{'id': 666666666, 'first_name': 'Аленатест', 'last_name': 'Тест'},
     {'id': 888888888, 'first_name': 'Валератест', 'last_name': 'Тест'}])
def test_upload_partner_info(user_id, partner_info):
    '''Тест функции upload_partner_info.
    '''
    Database.upload_partner_info(user_id, partner_info)
    partner_id = partner_info['id']
    partner_info_pattern ={
        'id_partner': partner_id,
        'link': f'https://vk.com/id{partner_id}',
        'first_name': partner_info['first_name'],
        'last_name': partner_info['last_name']
    }
    result = Database.session.query(Partners).\
        filter(Partners.id_partner == partner_id).scalar()
    result_func = {column: getattr(result, column) for column in result.__table__.c.keys()}
    assert result_func == partner_info_pattern

    DataManager.test_new_partners.append(result_func)

    result = Database.session.query(UsersPartners).\
        filter(UsersPartners.id_partner == partner_id,
               UsersPartners.id_user == user_id).scalar()
    assert result.id_user == user_id
    assert result.id_partner == partner_id


@pytest.mark.parametrize(
    'partner_id', 
    [info['id_partner'] for info in DataManager.test_partners_info])
def test_check_prkey_in_partners(partner_id):
    '''Тест функции check_prkey_in_partners.
    '''
    result_func = Database.check_prkey_in_partners(partner_id)
    assert result_func is True


@pytest.mark.parametrize(
    'user_id, partner_id, result_manual',
    [(DataManager.test_users_info[0]['id_user'], DataManager.test_partners_info[0]['id_partner'], False),
     (DataManager.test_users_info[0]['id_user'], DataManager.test_partners_info[1]['id_partner'], True)])
def test_check_ignore(user_id, partner_id, result_manual):
    '''Тест функции check_ignore.
    '''
    result_func = Database.check_ignore(user_id, partner_id)
    assert result_func is result_manual


def test_get_favorite_partners():
    '''Тест функции get_favorite_partners.
    '''
    result_func = Database.get_favorite_partners(
        DataManager.test_users_info[0]['id_user'])
    assert isinstance(result_func, list)
    assert len(result_func) >= 2
