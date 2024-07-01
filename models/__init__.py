from config import DATA
from .base import db
from .hpcounter import HpCounter
from .guild import Guild
import logging
log = logging.getLogger(__name__)

tables = [HpCounter, Guild]

if not (DATA/'database.db').exists():
    log.info("Creating database...")
    with db:
        db.create_tables(tables)