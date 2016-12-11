from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.contrib.botan import Botan
from config import BUYPROTECT, ALLTESTS, BOTAN_TOKEN
from pyexcel_xlsx import get_data, save_data
from itertools import zip_longest
from collections import OrderedDict
import logging
from datetime import datetime as dt
import os
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

aliases = [Aliases.alias1,
           Aliases.alias2,
           Aliases.alias3,
           Aliases.alias4,
           Aliases.alias5,
           Aliases.alias6,
           Aliases.alias7,
           Aliases.alias8,
           Aliases.alias9,
           Aliases.alias10]

botan = Botan(BOTAN_TOKEN)

search_fckup_msg = '''Мы не нашли совпадений, но приняли заявку на проверку!

Признаки недобросовестного Интернет-магазина:
- Отсутствие на сайте юридического или фактического адреса;
- Отсутствие на сайте официального названия продавца (например, ООО "Ромашка", ИП Иванов и т.п.);
- Администратор домена отличается от компании, указанной на сайте (можно проверить через https://www.reg.ru/whois/).

Признаки недобросовестной рекламы:
- Сноски, "звездочки" и оговорки мелким шрифтом;
- Утверждения "самый", "лучший", "первый";
- Негативная информация про конкурентов;
- Заявления об одобрении органами власти.

Будем рады выполнить другой запрос!'''


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
    msg = 'Привет! Я буду защищать тебя от обмана в рекламе и помогу с безопасным выбором мест для покупки товаров и услуг. ' \
          'В моей базе - несколько сотен компаний и рекламных роликов и она постоянно пополняется. ' \
          'Для поиска просто введи название компании, рекламного ролика, товара или фразы из рекламы. ' \
          'Если информации не будет в базе, мы получим твой запрос и организуем проверку'
    try:
        before_request_handler()
        Users.get(Users.telegram_id == uid)
    except DoesNotExist:
        Users.create(telegram_id=uid, username=username, name=name)
    after_request_handler()
    if uid in ADMINS:
        bot.sendMessage(uid, msg)
        return
    bot.sendMessage(uid, msg)


def search_wo_cat(bot, update):
    print(update)
    uid = update.message.from_user.id
    message = update.message.text.strip('"\'!?[]{},. ').lower()
    res = []
    msg = ''
    try:
        check_aliases = (Aliases.select().where((fn.lower(Aliases.alias1) == message) |
                                                (fn.lower(Aliases.alias2) == message) |
                                                (fn.lower(Aliases.alias3) == message) |
                                                (fn.lower(Aliases.alias4) == message) |
                                                (fn.lower(Aliases.alias5) == message) |
                                                (fn.lower(Aliases.alias6) == message) |
                                                (fn.lower(Aliases.alias7) == message) |
                                                (fn.lower(Aliases.alias8) == message) |
                                                (fn.lower(Aliases.alias9) == message) |
                                                (fn.lower(Aliases.alias10) == message))).execute()
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
        columns = ('name', 'description', 'url')
        for sheet in sheets:
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


updater = Updater(BUYPROTECT)
dp = updater.dispatcher
dp.add_handler(CommandHandler('start', start))
dp.add_handler(CommandHandler('unload', output))
dp.add_handler(MessageHandler(Filters.text, search_wo_cat))
dp.add_handler(MessageHandler(Filters.document, process_file))
updater.start_polling()
updater.idle()

