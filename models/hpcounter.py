from peewee import IntegerField, CharField, SqliteDatabase, Model
from models.base import Base
import logging
log = logging.getLogger(__name__)


class HpCounter(Base):
    name = CharField()
    owner = IntegerField()
    guild = IntegerField(null=True)
    wounds = IntegerField(default=0)