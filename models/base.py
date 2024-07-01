
from peewee import IntegerField, CharField, SqliteDatabase, Model
from config import DATA
import logging
log = logging.getLogger(__name__)

db = SqliteDatabase(DATA/'database.db')

class Base(Model):
    class Meta:
        database = db

def create_tables(tables):
    with db:
        db.create_tables(tables)