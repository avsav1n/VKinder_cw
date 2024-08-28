'''
Модуль инициализации логгирования.

'''

import functools
import logging
import os


def logging_init():
    '''Функция инициализации логгирования.
    
    '''
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'progress.log'),
                        filemode='a',
                        encoding='utf-8',
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%d-%m-%Y %H:%M:%S')


def logging_decorator(old_func):
    '''Декоратор для логгирования результатов выполнения функций.
    
    '''
    @functools.wraps(old_func)
    def new_func(*args, **kwargs):
        logging_params = {'old_func': old_func.__name__,
                        'args': args[1:], 
                        'kwargs': kwargs,
                        'spaces': ' ' * 25}
        logging.info('Запущена функция %(old_func)s\n%(spaces)sАргументы: %(args)s, %(kwargs)s',
                     logging_params)
        result = old_func(*args, **kwargs)
        if result:
            logging.info('Результат выполнения: %(result)s', {'result': result})
        return result
    return new_func

logging_init()
