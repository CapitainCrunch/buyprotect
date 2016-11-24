from peewee import *
from datetime import datetime
from config import MYSQL_CONN

db = MySQLDatabase(**MYSQL_CONN)

def before_request_handler():
    db.connect()

def after_request_handler():
    db.close()

class BaseModel(Model):
    class Meta:
        database = db

class Users(BaseModel):
    id = PrimaryKeyField()
    telegram_id = IntegerField(unique=1)
    username = CharField(default=None)
    name = CharField()
    dt = DateTimeField(default=datetime.now())


class Company(BaseModel):
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class Good(BaseModel):
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class Service(BaseModel):
    id = PrimaryKeyField()
    name = CharField(unique=1)
    description = TextField()
    url = CharField(default=None)
    dt = DateTimeField(default=datetime.now())


class UndefinedRequests(BaseModel):
    id = PrimaryKeyField()
    from_user = ForeignKeyField(Users,
                                  to_field='telegram_id')
    request = CharField()
    dt = DateTimeField(default=datetime.now())


class Aliases(BaseModel):
    id = PrimaryKeyField()
    key = CharField(unique=1)
    alias1 = CharField(default=None)
    alias2 = CharField(default=None)
    alias3 = CharField(default=None)
    alias4 = CharField(default=None)
    alias5 = CharField(default=None)
    alias6 = CharField(default=None)
    alias7 = CharField(default=None)
    alias8 = CharField(default=None)
    alias9 = CharField(default=None)
    alias10 = CharField(default=None)
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