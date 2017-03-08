from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.contrib.botan import Botan
from config import BUYPROTECT, ALLTESTS, BOTAN_TOKEN
from utils import get_alias_match
from pyexcel_xlsx import get_data, save_data
from itertools import zip_longest
from collections import OrderedDict
import logging
from datetime import datetime as dt
import os
import sys
from model import save, Users, \
    UndefinedRequests, Company, Good, Service, Aliases, DoesNotExist, fn, \
    before_request_handler, after_request_handler

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.basicConfig(filename='logs.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ADMINS = [209743126, 56631662, 214688324]

dbs = {'Компания': Company,
       'Услуга': Service,
       'Товар': Good,
       'Алиасы': Aliases}

SEARCH = 1
user_search = dict()



botan = Botan(BOTAN_TOKEN)

start_msg = '''Вас приветствует автоматический помощник для персонала магазинов, позволяющий оперативно решать юридические вопросы.

Например, чтобы проверить, входит ли товар в тот или иной перечень (есть ли для товара специальные условия возврата или обмена), введите его название, например "утюг", "телевизор", "планшет" и т.п.

Помощник позволит получить информацию по общим вопросам ("срок ремонта", "проверка качества", "возврат товара" и т.п.), ознакомиться с установленными перечнями товаров ("перечень технически сложных товаров", "перечень товаров надлежащего качества, не подлежащих возврату или обмену"), получить последнюю редакцию закона о защите прав потребителей или правил торговли ("закон о защите прав потребителей", "правила торговли").

В случае проверки помощник проинформирует о порядке действий ("проверка", "ход проверки", "ответы проверяющим" и т.п.) и предоставит контакты уполномоченных лиц ("служба безопасности").

Если интересующей информации нет в базе, операторы получат Ваш запрос и внесут необходимые сведения.

Помощник может быть запущен в браузере на компьютере (https://web.telegram.org/) или через приложение для компьютера (https://desktop.telegram.org/).'''


search_fckup_msg = '''Информация по Вашему запросу пока отсутствует в базе. Операторы добавят необходимые сведения в течение 24 часов.

Чтобы проверить, входит ли товар в тот или иной перечень (есть ли для товара специальные условия возврата или обмена), введите его название, например "утюг", "телевизор", "планшет" и т.п.

Помощник позволяет получить информацию по общим вопросам ("срок ремонта", "проверка качества", "возврат товара" и т.п.), ознакомиться с установленными перечнями товаров ("перечень технически сложных товаров", "перечень товаров надлежащего качества, не подлежащих возврату или обмену"), получить последнюю редакцию закона о защите прав потребителей или правил торговли ("закон о защите прав потребителей", "правила торговли").

В случае проверки помощник информирует о порядке действий ("проверка", "ход проверки", "ответы проверяющим" и т.п.) и предоставляет контакты уполномоченных лиц ("служба безопасности").'''


def unknown_req_add(tid, txt):
    before_request_handler()
    try:
        UndefinedRequests.get(fn.lower(UndefinedRequests.request) == txt.lower())
        UndefinedRequests.create(from_user=tid, request=txt)
    except DoesNotExist:
        UndefinedRequests.create(from_user=tid, request=txt)
        after_request_handler()
        return True
    after_request_handler()
    return False


def start(bot, update):
    print(update)
    username = update.message.from_user.username
    name = update.message.from_user.first_name
    uid = update.message.from_user.id
    try:
        before_request_handler()
        Users.get(Users.telegram_id == uid)
    except DoesNotExist:
        Users.create(telegram_id=uid, username=username, name=name)
    after_request_handler()
    if uid in ADMINS:
        bot.sendMessage(uid, start_msg, disable_web_page_preview=True)
        return
    bot.sendMessage(uid, start_msg, disable_web_page_preview=True)


def search_wo_cat(bot, update):
    print(update)
    uid = update.message.from_user.id
    message = update.message.text.strip('"\'!?[]{},. ').lower()
    res = []
    msg = ''
    try:
        check_aliases = get_alias_match(message)
        alias = [c.key for c in check_aliases]
        if alias:
            message = alias[0]
    except DoesNotExist:
        pass

    for model in dbs.values():
        if model == Aliases:
            continue
        before_request_handler()
        try:
            search = model.get(fn.lower(model.name) == message.lower())
            res.append(search)
        except DoesNotExist:
            pass
        after_request_handler()
    if not res:
        if unknown_req_add(uid, message.strip('"\'!?[]{},. ')):
            bot.sendMessage(uid, search_fckup_msg, disable_web_page_preview=True)
            # send to Oleg
            bot.send_message(214688324, 'Кто-то искал <b>{}</b> и не нашел'.format(message),
                             parse_mode=ParseMode.HTML)
        else:
            bot.sendMessage(uid, search_fckup_msg, disable_web_page_preview=True)
            return
    for m in res:
        msg += '<b>{}</b>\n{}\n{}\n\n'.format(m.name, m.description, m.url)
    bot.sendMessage(uid, msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    botan.track(update.message, event_name='search_wo_cat')


def process_file(bot, update):
    print(update)
    uid = update.message.from_user.id
    if uid in ADMINS:
        file_id = update.message.document.file_id
        fname = update.message.document.file_name
        newFile = bot.getFile(file_id)
        newFile.download(fname)
        sheets = get_data(fname)
        for sheet in sheets:
            columns = ('name', 'description', 'url')
            if sheet.lower() == 'алиасы':
                columns = ['key', 'alias1', 'alias2', 'alias3', 'alias4', 'alias5', 'alias6', 'alias7', 'alias8', 'alias9', 'alias10']
            _data = []
            for row in sheets[sheet][1:]:
                if not row:
                    continue
                _data.append(dict(zip_longest(columns, [r.strip('"\'!?[]{},. \n') for r in row], fillvalue='')))
            if save(_data, dbs[sheet]):
                bot.sendMessage(uid, 'Данные на странице {} сохранил'.format(sheet), disable_notification=1)
            else:
                bot.sendMessage(uid, 'Что-то не так с данными')
        os.remove(fname)


def clear(bot, update):
    uid = update.message.from_user.id
    if uid not in ADMINS:
        return
    if UndefinedRequests.table_exists():
        UndefinedRequests.drop_table()
    UndefinedRequests.create_table()
    bot.send_message(uid, 'Таблицу очистил')


def output(bot, update):
    print(update)
    uid = update.message.from_user.id
    if uid not in ADMINS:
        return
    foud = OrderedDict()
    before_request_handler()
    res = UndefinedRequests.select(UndefinedRequests.request, fn.COUNT(UndefinedRequests.id).alias('count')).\
        group_by(UndefinedRequests.request).execute()
    after_request_handler()
    foud.update({'Отсутствия в базе': [(r.request, r.count) for r in res]})
    fname = str(dt.now()) + '.xlsx'
    save_data(fname, foud)
    bot.sendDocument(uid, document=open(fname, 'rb'))
    os.remove(fname)


if __name__ == '__main__':
    updater = None
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[-1]
        if token.lower() == 'buy':
            updater = Updater(BUYPROTECT)
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            logging.basicConfig(filename=BASE_DIR + '/out.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    else:
        updater = Updater(ALLTESTS)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('clear', clear))
    dp.add_handler(CommandHandler('unload', output))
    dp.add_handler(MessageHandler(Filters.text, search_wo_cat))
    dp.add_handler(MessageHandler(Filters.document, process_file))
    updater.start_polling()
    updater.idle()

