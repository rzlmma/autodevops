import os
import logging.handlers
from flask import Flask
from flask_appbuilder import SQLA, AppBuilder


"""
 Logging configuration
"""
log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs/app.log")
logger = logging.getLogger()
hander = logging.handlers.TimedRotatingFileHandler(filename=log_file_path, when='d',
                                                   interval=1, backupCount=7)
fmt = '%(asctime)s  %(levelname)s  %(filename)s:%(lineno)s  %(funcName)s  %(message)s'

formatter = logging.Formatter(fmt)
hander.setFormatter(formatter)
logger.addHandler(hander)
logger.setLevel(logging.INFO)

app = Flask(__name__)
app.config.from_object('config')
db = SQLA(app)
appbuilder = AppBuilder(app, db.session)
# scheduler.start()

"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""    

from app import views

