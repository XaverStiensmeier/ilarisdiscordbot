from peewee import IntegerField, CharField, SqliteDatabase, Model
from config import DATA
import logging
log = logging.getLogger(__name__)

db = SqliteDatabase(DATA/'database.db')

def create_tables():
    with db:
        db.create_tables([Hpcounter])

class Base(Model):
    class Meta:
        database = db

class Hpcounter(Base):
    name = CharField()
    owner = IntegerField()
    guild = IntegerField(null=True)
    wounds = IntegerField(default=0)

if not (DATA/'database.db').exists():
    create_tables()