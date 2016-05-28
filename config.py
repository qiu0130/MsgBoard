
from datetime import timedelta
class Config(object):

    _SQL_PARAMS = {
        'pwd': '123456',
        'host': '127.0.0.1',
        'db': 'msg',
        'port': 3306,
        'user': 'root',
        }

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://%s:%s@%s:%s/%s" % (_SQL_PARAMS['user'],
                                                      _SQL_PARAMS['pwd'],
                                                      _SQL_PARAMS['host'],
                                                      _SQL_PARAMS['port'],
                                                      _SQL_PARAMS['db'])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _REDIS_PARAMS = {
        "pwd": "",
        "host": "127.0.0.1",
        "db": 0,
        "port": 6379
    }
    REDIS_URL = "redis://:%s@%s:%s/%s" % (_REDIS_PARAMS['pwd'],
                                          _REDIS_PARAMS['host'],
                                          _REDIS_PARAMS["port"],
                                          _REDIS_PARAMS["db"])
    DEBUG = False
    TESTING = False
    SECRET_KEY = b"\xc5\rp\xab\xf5\xf0\xe5\x0c<&\xcc\xdb\x93\xa4\\\xc8\xbf\x83\tS\x1e\xff\xcc\x9e"
    PERMANENT_SESSION_LIFETIME = timedelta(seconds = 60 * 10)


class ProductionConfig(Config):
    DEBUG = False
    _SQL_PARAMS = {
        'pwd': '123456',
        'host': '127.0.0.1',
        'db': 'msg',
        'port': 3306,
        'user': 'root',
        }

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://%s:%s@%s:%s/%s" % (_SQL_PARAMS['user'],
                                                      _SQL_PARAMS['pwd'],
                                                      _SQL_PARAMS['host'],
                                                      _SQL_PARAMS['port'],
                                                      _SQL_PARAMS['db'])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _REDIS_PARAMS = {
        "pwd": "redis",
        "host": "127.0.0.1",
        "db": 0,
        "port": 6379
    }
    REDIS_URL = "redis://:%s@%s:%s/%s" % (_REDIS_PARAMS['pwd'],
                                          _REDIS_PARAMS['host'],
                                          _REDIS_PARAMS["port"],
                                          _REDIS_PARAMS["db"])

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
