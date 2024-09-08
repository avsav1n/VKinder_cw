'''
Основной модуль, описывающий логику работы бота Vk-сообщества
и его взаимодействия с базой данных PostgreSQL.

'''
from collections.abc import Generator
from datetime import datetime
from random import randrange
import logging

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.tools import VkTools

from extrapacks.config import VKGROUP_TOKEN, VKUSER_TOKEN
from extrapacks.logging_functions import logging_decorator
from models import Genders, Users, Partners, UsersPartners, DatabaseConfig


class Database:
    '''Статический класс для взаимодействия с базой данных PostgreSQL.

       Для работы с базой данных в файл config.py необходимо ввести параметры подключения.
    
    '''
    session = DatabaseConfig.Session()

    @logging_decorator
    @staticmethod
    def get_gender(name: str) -> int:
        '''Функция выборки пола человека, соответствующего его имени из таблицы "genders".
        
        '''
        name = name.capitalize().replace('ё', 'е')
        result = Database.session.query(Genders.sex).\
            filter(Genders.name == name).scalar()
        return result


    @logging_decorator
    @staticmethod
    def get_users() -> dict:
        '''Функция выборки идентификаторов всех пользователей из таблицы "users".

           Используется для заполнения оперативного словаря users_state 
           после перезапуска программы.
        
        '''
        result = {id.id_user: {} for id in Database.session.query(Users.id_user).all()}
        return result


    @logging_decorator
    @staticmethod
    def get_user_info(user_id: int) -> dict:
        '''Функция выборки всей информации о пользователе из таблицы "users".
        
        '''
        result = Database.session.query(Users).\
            filter(Users.id_user == user_id).scalar()
        return {column: getattr(result, column) for column in result.__table__.c.keys()}

    @logging_decorator
    @staticmethod
    def upload_user_info(user_info: dict):
        '''Функция записи информации о пользователе в таблицу "users".
        
        '''
        model = Users(**user_info)
        Database.session.add(model)
        Database.session.commit()


    @logging_decorator
    @staticmethod
    def upload_relationship(user_id: int, partner_id: int, ignore=False):
        '''Функция добавления отношения между существующим пользователем и 
           существующим парнером в таблицу "users_partners".
        
        '''
        model = UsersPartners(id_user=user_id, id_partner=partner_id, ignore=ignore)
        Database.session.add(model)
        Database.session.commit()


    @logging_decorator
    @staticmethod
    def upload_partner_info(user_id: int, partner_info: dict, ignore=False):
        '''Функция записи информации о партнере в таблицы "users" и "users_partners".
        
        '''
        partner_id = partner_info['id']

        if Database.check_prkey_in_partners(partner_id):
            if Database.check_prkey_in_users_partners(user_id, partner_id):
                return
            Database.upload_relationship(user_id, partner_id, ignore=ignore)
            return

        partner_info ={
            'id_partner': partner_id,
            'link': f'https://vk.com/id{partner_id}',
            'first_name': partner_info['first_name'],
            'last_name': partner_info['last_name']
        }
        model = Partners(**partner_info)
        model.users_partners = [UsersPartners(id_user=user_id, ignore=ignore)]
        Database.session.add(model)
        Database.session.commit()


    @logging_decorator
    @staticmethod
    def check_ignore(user_id: int, partner_id: int) -> bool:
        '''Функция проверки наличия флага ignore в таблице "users_partners".
        
        '''
        result = Database.session.query(UsersPartners.ignore).\
            filter(UsersPartners.id_user == user_id, 
                   UsersPartners.id_partner == partner_id).scalar()
        return bool(result)


    @logging_decorator
    @staticmethod
    def check_prkey_in_partners(partner_id: int) -> bool:
        '''Функция проверки наличия записи о партнере в таблице "partners".
        
        '''
        result = Database.session.query(Partners.id_partner).\
            filter(Partners.id_partner == partner_id).scalar()
        return bool(result)


    @logging_decorator
    @staticmethod
    def check_prkey_in_users_partners(user_id: int, partner_id: int) -> bool:
        '''Функция проверки наличия записи о пользователе и партнере в таблице "users_partners".
        
        '''
        result = Database.session.query(UsersPartners.id_user).\
            filter(UsersPartners.id_user == user_id,
                   UsersPartners.id_partner == partner_id).scalar()
        return bool(result)


    @logging_decorator
    @staticmethod
    def get_favorite_partners(user_id: int):
        '''Функция выборки информации об избранных партнерах пользователя из таблицы "partners".

        '''
        result = Database.session.query(Partners).\
            with_entities(Partners.first_name, Partners.last_name, Partners.link).\
            join(UsersPartners.partners).\
            filter(UsersPartners.id_user == user_id, UsersPartners.ignore == False).all()
        return result


class Buttons:
    '''Класс регистрация кнопок пользователя для интерфейса бота Vk-сообщества.
       
       В зависимости от цвета темы светлая/темная, цвет кнопок также меняется:
        POSITIVE - зеленая/зеленая
        NEGATIVE - красная/красная
         PRIMARY - синяя/белая
       SECONDARY - белая/серая

    '''
    # button (кнопки с текстом)
    start_searching_label = 'Начать поиск \U0001F495'
    start_searching = {'label': start_searching_label,
                       'color': VkKeyboardColor.SECONDARY}
    
    repeat_label = 'Повторить \U0000267B'
    repeat = {'label': repeat_label,
              'color': VkKeyboardColor.SECONDARY}
    
    like_label = '\U0001F44D'
    like = {'label': like_label,
            'color': VkKeyboardColor.POSITIVE}
    
    dislike_label = '\U0001F44E'
    dislike = {'label': dislike_label,
               'color': VkKeyboardColor.NEGATIVE}
    
    next_partner_label = 'Далее \U0001F500'
    next_partner = {'label': next_partner_label,
                    'color': VkKeyboardColor.SECONDARY}
    
    favorites_label = 'Показать понравившихся \U0001F60D'
    favorites = {'label': favorites_label,
               'color': VkKeyboardColor.POSITIVE}
    
    update_label = 'Начать сначала \U0001F504'
    update = {'label': update_label,
              'color': VkKeyboardColor.SECONDARY}

    # openlink_button (кнопки с ссылкой)
    github_link = {'label': 'Репозиторий в GitHub \U0001F40D',
                   'link': 'https://github.com/avsav1n/Telebot_cw'}
    

    @staticmethod
    def get_main_navigation_keyboard() -> VkKeyboard:
        '''Метод формирования основных навигационных кнопок.
        
        '''
        keyboard = VkKeyboard()
        keyboard.add_button(**Buttons.next_partner)
        keyboard.add_line()
        keyboard.add_button(**Buttons.update)
        keyboard.add_button(**Buttons.favorites)
        return keyboard
    
    @staticmethod
    def get_inline_reactions_keyboard() -> VkKeyboard:
        '''Метод формирования кнопок реакций на предлагаемых партнеров.
        
        '''
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button(**Buttons.dislike)
        keyboard.add_button(**Buttons.like)
        return keyboard


class VkontakteAPI(vk_api.VkApi):
    '''Класс для работы с API Вконтакте.

       Для подключения к API необходимо в файл config.py ввести имеющийся токен сообщества.

    '''
    def __init__(self, token):
        '''Конструктор класса.

        '''
        super().__init__(token=token)
        self.api_user_token = vk_api.VkApi(token=VKUSER_TOKEN)
        self.user_state = {}

        # 1 - female, 2 - male
        self.invert_genders = {1: 2, 2: 1}


    @logging_decorator
    def get_user_info(self, user_id: int) -> dict:
        '''Метод запроса и обработки информации о пользователе.
           
           Запрос к API осуществляется методом "users.get".
        
        '''
        response = self.method('users.get', {'user_ids': user_id,
                                             'fields': 'city, bdate, sex'})[0]
        if (bdate := response.get('bdate')):
            bdate = datetime.strptime(bdate, '%d.%m.%Y')
            age = (datetime.now().year - bdate.year -
               ((datetime.now().month, datetime.now().day) < (bdate.month, bdate.day)))

        sex = response.get('sex')
        if sex == 0: # API возвращает 0 если пол не указан
            sex = Database.get_gender(response['first_name'])

        if (city := response.get('city')):
            city = city['id']

        user_info = {
            'id_user': user_id,
            'id_city': city,
            'age': age,
            'sex': sex
        }
        return user_info


    @logging_decorator
    def find_all_partners(self, user_info: dict) -> Generator:
        '''Метод поиска партнеров.
        
           Запрос к API осуществляется методом "users.search".

        '''
        params = {
            'sex': self.invert_genders[user_info['sex']],
            'city': user_info['id_city'],
            'age_from': user_info['age'] - 5,
            'age_to': user_info['age'] + 5,
            'status': 6, # в активном поиске
            'has_photo': 1,
        }
        all_partners = VkTools(self.api_user_token).\
                                get_all_iter('users.search',
                                max_count=1000, values=params)
        user_id = user_info['id_user']
        self.user_state[user_id]['all_partners'] = all_partners


    @logging_decorator
    def get_partner_photos(self, partner_id: int) -> Generator:
        '''Метод запроса и обработки фотографий партнера.
        
        '''
        params = {
            'owner_id': partner_id,
            'album_id': 'profile',
            'extended': '1'
        }
        photos_info = self.api_user_token.method('photos.get', params)
        photos_info = sorted(photos_info['items'], key=lambda x: x['likes']['count'])[-3:]
        photos_id = (photo['id'] for photo in photos_info)

        return photos_id


    @logging_decorator
    def get_partner(self, user_id: int):
        '''Метод обработки инфомации о следующем партнере из генератора find_all_partners.

           Для временного хранения данных о просматриваемом партнере для последующего 
           взаимодействия с ними, выгружает всю собранную информацию в словарь user_state.
        
        '''
        while True:
            try:
                partner_info = next(self.user_state[user_id]['all_partners'])
            except KeyError:
                user_info = Database.get_user_info(user_id)
                self.find_all_partners(user_info)
                partner_info = next(self.user_state[user_id]['all_partners'])

            if not (partner_info['first_name'].isalpha() and 
                    partner_info['last_name'].isalpha()):
                continue

            partner_id = partner_info['id']
            if not Database.check_ignore(user_id, partner_id):
                break

        photos_id = self.get_partner_photos(partner_id)

        partner_info = {key: value for key, value in partner_info.items() 
                        if key in ('id', 'first_name', 'last_name')}
        partner_info['photos_id'] = photos_id
        self.user_state[user_id]['current_partner'] = partner_info


class VkontakteBot(VkontakteAPI):
    '''Класс для взаимодействия с ботом VK-сообщества.

       Для подключения к боту необходимо в файл config.py ввести имеющийся токен сообщества.

    '''
    def __init__(self, token=VKGROUP_TOKEN):
        '''Конструктор класса.

        '''
        super().__init__(token=token)


    def __call__(self):
        '''Метод активации опроса серверов ВКонтакте на наличие новых сообщений.

        '''
        longpoll = VkLongPoll(self)

        self.user_state.update(Database.get_users())

        print('Bot is running...')
        logging.warning('Бот Vk-сообщества запущен')

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == 'Стоп':
                    print('Bot stopped from chat.')
                    logging.warning('Бот Vk-сообщества остановлен из чата\n')
                    break
                self.start_handling(event)

        Database.session.close()


    def send_message(self, user_id: int, message: str,
                     keyboard: VkKeyboard=None, attachment: str=None):
        '''Метод отправки сообщений в чат пользователю.

        '''
        if keyboard is not None:
            keyboard = keyboard.get_keyboard()
        self.method('messages.send', {'user_id': user_id,
                                      'message': message, 
                                      'keyboard': keyboard,
                                      'attachment': attachment,
                                      'random_id': randrange(10 ** 7)})


    def show_favorite_partners(self, user_id: int):
        '''Функция-обработчик сообщения 'Показать понравившихся'.

           Выводит пользователю всех понравившихся ранее ему партнеров.
        
        '''
        favorite_partners = Database.get_favorite_partners(user_id)
        if not favorite_partners:
            self.show_if_favorite_partners_empty(user_id)
            return

        message = 'Вам понравились следующие люди \U0001F60A'

        keyboard = Buttons.get_main_navigation_keyboard()
        self.send_message(user_id, message=message, keyboard=keyboard)

        for partner in favorite_partners:
            message = f'{partner.first_name} {partner.last_name}\n{partner.link}'
            self.send_message(user_id, message=message, keyboard=keyboard)


    def show_if_favorite_partners_empty(self, user_id: int):
        '''Метод отправки в чат пользователю предупреждения, что его список 
           понравившихся партнеров пуст. 

        '''
        message = ('В настоящее время список понравившихся Вам людей пуст \U00002639\n'
                   'Продолжайте поиски! Никогда не поздно влюбиться \U0001F609')
        keyboard = Buttons.get_main_navigation_keyboard()
        self.send_message(user_id, message=message, keyboard=keyboard)


    def show_not_enought_profile_info(self, user_id: int):
        '''Метод отправки в чат пользователю предупреждения, что указанной информации в его 
           профиле недостаточно для осуществления поиска партнера.
        
        '''
        message = ('К сожалению, в настоящее время для продолжения работы '
                   'в Вашем профиле недостаточно \U0000274C данных для осуществления '
                   'корретного поиска партнера. Пожалуйста, укажите минимально необходимую '
                   'информацию (пол, город, дату рождения) и повторите попытку! \U0001F575')
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(**Buttons.repeat)
        self.send_message(user_id, message=message, keyboard=keyboard)


    def show_greeting(self, user_id: int):
        '''Метод отправки в чат пользователю приветствия.
        
        '''
        message = ('Доброго времени суток! \U0001F44B\n'
                   'Я - бот \U0001F916 сообщества поиска своей второй половины \U0001F48F')
        keyboard = VkKeyboard(inline=True)
        keyboard.add_openlink_button(**Buttons.github_link)
        self.send_message(user_id, message=message, keyboard=keyboard)

        self.greeting_handling(user_id)


    def reaction_like_handling(self, user_id: int):
        '''Функция-обработчик реакции 'Лайк' пользователя на отображаемого партнера.

           В соответствии с логикой работы, добавляет партнера в базу данных, помечает его
           флагом ignore=False. Фактически осуществляется добавления партнера в избранное.
        
        '''
        Database.upload_partner_info(user_id, self.user_state[user_id]['current_partner'])
        self.show_found_people(user_id)


    def reaction_dislike_handling(self, user_id: int):
        '''Функция-обработчик реакции 'Дизлайк' пользователя на отображаемого партнера.

           В соответствии с логикой работы, добавляет партнера в базу данных, помечает его
           флагом ignore=True, после чего данный партнер больше не будет попадаться пользователю
           при поиске.
        
        '''
        Database.upload_partner_info(user_id, self.user_state[user_id]['current_partner'], True)
        self.show_found_people(user_id)


    def greeting_handling(self, user_id: int):
        '''Функция-обработчик сообщений 'Начать', 'Повторить'.

           Обрабатывает информацию о пользователе и формирует интерфейс взаимодействия.
        
        '''
        if user_id not in self.user_state:
            user_info = super().get_user_info(user_id)
            if not all(user_info.values()):
                self.show_not_enought_profile_info(user_id)
                return
            Database.upload_user_info(user_info)
            self.user_state[user_id] = {}

        message = ('Для того, чтобы начать поиск нажмите на кнопочку ниже \U0001F447'
                   'Поиск будет осуществлен по таким параметрам как\n'
                   'пол (куда же без него?), город и возраст \U0001F50E.\n'
                   'Для чистоты поиска, пожалуйста, убедитесь что в Вашем профиле ' 
                   'указаны данные параметры \U0001F64F\nНачнем же? \U0001F942')
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(**Buttons.start_searching)
        self.send_message(user_id, message=message, keyboard=keyboard)


    def show_found_people(self, user_id: int):
        '''Метод отправки в чат пользователю найденного партнера.

           Выполняется из функции start_searching_handling или при получении команды 'Далее'
           при условии что ранее выполнен поиск всех подходящих партнеров find_all_partners.

        '''
        super().get_partner(user_id)

        partner_id = self.user_state[user_id]['current_partner']['id']
        message = (f'{self.user_state[user_id]['current_partner']['first_name']} '
                   f'{self.user_state[user_id]['current_partner']['last_name']}\n'
                   f'https://vk.com/id{partner_id}')

        keyboard = Buttons.get_inline_reactions_keyboard()

        attachment = ''
        for photo_id in self.user_state[user_id]['current_partner']['photos_id']:
            attachment += f'photo{partner_id}_{photo_id},'

        self.send_message(user_id, message=message, keyboard=keyboard, attachment=attachment)


    def start_searching_handling(self, user_id: int):
        '''Функция-обработчик сообщения 'Начать поиск', 'Начать сначала'

           Запускает процедуру поиска партнеров для знакомства с пользователем,
           а также формирует интерфейс для взаимодействия с результатами.

        '''
        user_info = Database.get_user_info(user_id)
        super().find_all_partners(user_info)

        keyboard = Buttons.get_main_navigation_keyboard()
        message = 'По Вашему запросу найдены следующие люди \U0001F970'
        self.send_message(user_id, message=message, keyboard=keyboard)

        self.show_found_people(user_id)


    def start_handling(self, event: Event):
        '''Основная функция-обработчик сообщений пользователя.
        
        '''
        user_id = event.user_id
        match event.text:
            case 'Начать':
                self.show_greeting(user_id)

            case Buttons.start_searching_label:
                logging.info('Получена команда %s', Buttons.start_searching_label)
                self.start_searching_handling(user_id)
            
            case Buttons.update_label:
                logging.info('Получена команда %s', Buttons.update_label)
                self.start_searching_handling(user_id)

            case Buttons.repeat_label:
                logging.info('Получена команда %s', Buttons.repeat_label)
                self.greeting_handling(user_id)

            case Buttons.next_partner_label:
                logging.info('Получена команда %s', Buttons.next_partner_label)
                self.show_found_people(user_id)

            case Buttons.like_label:
                logging.info('Получена команда %s', Buttons.like_label)
                self.reaction_like_handling(user_id)

            case Buttons.dislike_label:
                logging.info('Получена команда %s', Buttons.dislike_label)
                self.reaction_dislike_handling(user_id)

            case Buttons.favorites_label:
                logging.info('Получена команда %s', Buttons.favorites_label)
                self.show_favorite_partners(user_id)

            case _:
                self.send_message(user_id, 'Такой команды не знаю! \U0001F937')


if __name__ == '__main__':
    api_group_token = VkontakteBot()
    api_group_token()
