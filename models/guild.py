
from peewee import IntegerField, CharField, SqliteDatabase, Model
from models.base import Base
import logging
log = logging.getLogger(__name__)


class Guild(Base):
    guild = IntegerField(unique=True)
    admins = CharField(default='[]')
    info_channel = IntegerField(null=True)
    language = CharField(default="en")