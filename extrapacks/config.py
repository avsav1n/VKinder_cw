'''
Модуль констант для инициализации программы и 
ее подключения к боту VK-сообщества и базе данных PostgreSQL

'''
import os

# Токен VK-сообщества
VKGROUP_TOKEN = os.getenv('VKGROUPTOKEN')
VKUSER_TOKEN = os.getenv('VKUSERTOKEN')

# Параметры подключения к базе данных
DB_DRIVER = 'postgresql'
DB_LOGIN = 'postgres'
DB_PASSWORD = os.getenv('PSQLPASS')
DB_CONNECTION = 'localhost'
DB_PORT = '5432'
DB_NAME = 'VKinder'
