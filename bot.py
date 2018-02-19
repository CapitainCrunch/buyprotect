from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.contrib.botan import Botan
from config import BUYPROTECT, ALLTESTS, BOTAN_TOKEN
from utils import get_alias_match, log
from pyexcel_xlsx import get_data, save_data
from itertools import zip_longest
from collections import OrderedDict
import logging
from datetime import datetime as dt
import os
import sys
from model import save, Users, \
    UndefinedRequests, Company, Good, Service, Aliases, DoesNotExist, fn

ADMINS = [209743126, 56631662, 214688324]

dbs = {'Компания': Company,
       'Услуга': Service,
       'Товар': Good,
       'Алиасы': Aliases}

SEARCH = 1
user_search = dict()


botan = Botan(BOTAN_TOKEN)

start_msg = '''Привет! Я помогу тебе с безопасным выбором мест для покупки товаров и услуг и буду защищать от обмана в рекламе.

В моей базе - несколько сотен компаний и рекламных роликов и она постоянно пополняется.

Для поиска просто введи название компании, рекламного ролика или фразы из рекламы.

Можешь также задать вопросы по защите прав потребителей (например, «возврат товара», «проверка качества», «технически сложные товары» и т.п.).

Если информации не будет в базе, мы получим твой запрос и организуем проверку.'''


search_fckup_msg = '''Мы не нашли совпадений, но приняли заявку на проверку!

Признаки недобросовестного Интернет-магазина:
- Отсутствие на сайте юридического или фактического адреса;
- Отсутствие на сайте официального названия продавца (например, ООО "Ромашка", ИП Иванов и т.п.);
- Администратор домена отличается от компании, указанной на сайте (можно проверить через сервис whois).

Признаки недобросовестной рекламы:
- Сноски, "звездочки" и оговорки мелким шрифтом;
- Утверждения "самый", "лучший", "первый";
- Негативная информация про конкурентов;
- Заявления об одобрении органами власти.'''


def unknown_req_add(tid, txt):
    try:
        UndefinedRequests.get(fn.lower(UndefinedRequests.request) == txt.lower())
        UndefinedRequests.create(from_user=tid, request=txt)
    except DoesNotExist:
        UndefinedRequests.create(from_user=tid, request=txt)
        return True
    return False


@log
def start(bot, update):
    print(update)
    username = update.message.from_user.username
    name = update.message.from_user.first_name
    uid = update.message.from_user.id
    try:
        Users.get(Users.telegram_id == uid)
    except DoesNotExist:
        Users.create(telegram_id=uid, username=username, name=name)
    if uid in ADMINS:
        bot.sendMessage(uid, start_msg, disable_web_page_preview=True)
        return
    bot.sendMessage(uid, start_msg, disable_web_page_preview=True)


@log
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
        try:
            search = model.get(fn.lower(model.name) == message.lower())
            res.append(search)
        except DoesNotExist:
            pass
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


@log
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
                columns = ['key'] + ['alias' + str(i) for i in range(1, 101)]
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


@log
def clear(bot, update):
    uid = update.message.from_user.id
    if uid not in ADMINS:
        return
    if UndefinedRequests.table_exists():
        UndefinedRequests.drop_table()
    UndefinedRequests.create_table()
    bot.send_message(uid, 'Таблицу очистил')


@log
def clearbase(bot, update):
    uid = update.message.from_user.id
    if uid not in ADMINS:
        return
    try:
        Company.drop_table()
        Company.create_table()

        Service.drop_table()
        Service.create_table()

        Good.drop_table()
        Good.create_table()

        Aliases.drop_table()
        Aliases.create_table()
    except:
        bot.send_message(
            uid,
            'Что-то пошло не так. Не все таблицы очищены',
        )
        return
    bot.send_message(uid, 'Таблицу очистил')


@log
def output(bot, update):
    print(update)
    uid = update.message.from_user.id
    if uid not in ADMINS:
        return
    foud = OrderedDict()
    res = UndefinedRequests.select(UndefinedRequests.request, fn.COUNT(UndefinedRequests.id).alias('count')).\
        group_by(UndefinedRequests.request).execute()
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
    dp.add_handler(CommandHandler('clearbase', clearbase))
    dp.add_handler(CommandHandler('unload', output))
    dp.add_handler(MessageHandler(Filters.text, search_wo_cat))
    dp.add_handler(MessageHandler(Filters.document, process_file))
    updater.start_polling()
    updater.idle()

