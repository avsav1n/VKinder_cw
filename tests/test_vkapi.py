'''
Модуль тестирования класса VkontakteAPI модуля main.

'''
import sys
import os
sys.path.append(os.getcwd())
from collections.abc import Generator

import pytest

from main import VkontakteAPI
from extrapacks.config import VKUSER_TOKEN, VKGROUP_TOKEN


def test_get_user_info():
    '''Тест функции get_user_info.
    '''
    user_id = 863244386
    vkapi = VkontakteAPI(VKGROUP_TOKEN)
    result_func = vkapi.get_user_info(user_id)

    assert isinstance(result_func, dict)
    assert result_func['id_user'] == user_id

def test_find_all_partners():
    '''Тест функции find_all_partners.
    '''
    user_info = {
        'id_user': 863244386,
        'id_city': 1,
        'age': 25,
        'sex': 1
    }

    vkapi = VkontakteAPI(VKUSER_TOKEN)
    vkapi.user_state[863244386] = {}
    vkapi.find_all_partners(user_info)

    assert isinstance(vkapi.user_state[863244386]['all_partners'], Generator)

    partner_info = next(vkapi.user_state[863244386]['all_partners'])

    assert isinstance(partner_info, dict)

    counter = 0
    for partner in vkapi.user_state[863244386]['all_partners']:
        counter += 1
        if counter == 5:
            break
    
    assert counter >= 1

def test_get_partner():
    '''Тест функции get_partner.
    '''
    user_info = {
        'id_user': 863244386,
        'id_city': 1,
        'age': 25,
        'sex': 1
    }
    vkapi = VkontakteAPI(VKUSER_TOKEN)
    vkapi.user_state[863244386] = {}
    vkapi.find_all_partners(user_info)
    vkapi.get_partner(863244386)

    assert isinstance(vkapi.user_state[863244386]['current_partner'], dict)

def test_get_partner_photos():
    '''Тест функции get_partner_photos.
    '''
    vkapi = VkontakteAPI(VKUSER_TOKEN)
    result_func = vkapi.get_partner_photos(863244386)

    assert isinstance(result_func, Generator)

    result_func = list(result_func)

    assert len(result_func) == 3
    assert isinstance(result_func[0], int)
