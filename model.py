from peewee import *
from datetime import datetime
from config import MYSQL_CONN

from playhouse.shortcuts import RetryOperationalError
from playhouse.pool import MySQLDatabase


class MyRetryDB(RetryOperationalError, MySQLDatabase):
    pass


db = MyRetryDB('buyprotect', **MYSQL_CONN)


class Users:
    id = PrimaryKeyField()
    telegram_id = IntegerField(unique=1)
    username = CharField(default=None)
    name = CharField()
    dt = DateTimeField(default=datetime.now())


class Company:
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class Good:
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class Service:
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class UndefinedRequests:
    id = PrimaryKeyField()
    from_user = ForeignKeyField(Users,
                                to_field='telegram_id')
    request = CharField()
    dt = DateTimeField(default=datetime.now())


class Aliases:
    id = PrimaryKeyField()
    key = CharField(unique=1)
    alias1 = TextField(default=None)
    alias2 = TextField(default=None)
    alias3 = TextField(default=None)
    alias4 = TextField(default=None)
    alias5 = TextField(default=None)
    alias6 = TextField(default=None)
    alias7 = TextField(default=None)
    alias8 = TextField(default=None)
    alias9 = TextField(default=None)
    alias10 = TextField(default=None)
    alias11 = TextField(default=None)
    alias12 = TextField(default=None)
    alias13 = TextField(default=None)
    alias14 = TextField(default=None)
    alias15 = TextField(default=None)
    alias16 = TextField(default=None)
    alias17 = TextField(default=None)
    alias18 = TextField(default=None)
    alias19 = TextField(default=None)
    alias20 = TextField(default=None)
    alias21 = TextField(default=None)
    alias22 = TextField(default=None)
    alias23 = TextField(default=None)
    alias24 = TextField(default=None)
    alias25 = TextField(default=None)
    alias26 = TextField(default=None)
    alias27 = TextField(default=None)
    alias28 = TextField(default=None)
    alias29 = TextField(default=None)
    alias30 = TextField(default=None)
    alias31 = TextField(default=None)
    alias32 = TextField(default=None)
    alias33 = TextField(default=None)
    alias34 = TextField(default=None)
    alias35 = TextField(default=None)
    alias36 = TextField(default=None)
    alias37 = TextField(default=None)
    alias38 = TextField(default=None)
    alias39 = TextField(default=None)
    alias40 = TextField(default=None)
    alias41 = TextField(default=None)
    alias42 = TextField(default=None)
    alias43 = TextField(default=None)
    alias44 = TextField(default=None)
    alias45 = TextField(default=None)
    alias46 = TextField(default=None)
    alias47 = TextField(default=None)
    alias48 = TextField(default=None)
    alias49 = TextField(default=None)
    alias50 = TextField(default=None)
    alias51 = TextField(default=None)
    alias52 = TextField(default=None)
    alias53 = TextField(default=None)
    alias54 = TextField(default=None)
    alias55 = TextField(default=None)
    alias56 = TextField(default=None)
    alias57 = TextField(default=None)
    alias58 = TextField(default=None)
    alias59 = TextField(default=None)
    alias60 = TextField(default=None)
    alias61 = TextField(default=None)
    alias62 = TextField(default=None)
    alias63 = TextField(default=None)
    alias64 = TextField(default=None)
    alias65 = TextField(default=None)
    alias66 = TextField(default=None)
    alias67 = TextField(default=None)
    alias68 = TextField(default=None)
    alias69 = TextField(default=None)
    alias70 = TextField(default=None)
    alias71 = TextField(default=None)
    alias72 = TextField(default=None)
    alias73 = TextField(default=None)
    alias74 = TextField(default=None)
    alias75 = TextField(default=None)
    alias76 = TextField(default=None)
    alias77 = TextField(default=None)
    alias78 = TextField(default=None)
    alias79 = TextField(default=None)
    alias80 = TextField(default=None)
    alias81 = TextField(default=None)
    alias82 = TextField(default=None)
    alias83 = TextField(default=None)
    alias84 = TextField(default=None)
    alias85 = TextField(default=None)
    alias86 = TextField(default=None)
    alias87 = TextField(default=None)
    alias88 = TextField(default=None)
    alias89 = TextField(default=None)
    alias90 = TextField(default=None)
    alias91 = TextField(default=None)
    alias92 = TextField(default=None)
    alias93 = TextField(default=None)
    alias94 = TextField(default=None)
    alias95 = TextField(default=None)
    alias96 = TextField(default=None)
    alias97 = TextField(default=None)
    alias98 = TextField(default=None)
    alias99 = TextField(default=None)
    alias100 = TextField(default=None)
    dt = DateTimeField(default=datetime.now())


def init_db():
    tables = [Users, Company, Good, Service, UndefinedRequests, Aliases]
    for t in tables:
        if t.table_exists():
            t.drop_table()
        t.create_table()


def save(data, db_name):
    """
    Initialize table.
    Batch insert rows
    :param texts_stats:
    :return:
    """

    with db.atomic():
        db_name.insert_many(data).upsert().execute()
    return True


if __name__ == '__main__':
    init_db()
    print('Таблицы создал')
