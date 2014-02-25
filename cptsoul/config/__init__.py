# -*- coding: utf-8 -*-

import logging
import platform
import os
import user
from json import load, dump

from cptsoul.config.configtypes import nonEmptyStrJSON, boolJSON, intJSON, nonEmptyStrSetJSON, encodedStrJSON


class ConfigFile(object):
    def __init__(self, path=None):
        self._path = path or self.getPath()
        self._data = {}
        self.read()

    @staticmethod
    def getPath():
        if platform.system() == 'Linux':
            directory = os.path.join(user.home, '.config')
        elif platform.system() == 'Windows':
            directory = os.path.join(os.getenv('APPDATA'), 'Roaming')
        else:
            directory = './'
        return os.path.join(directory, 'cptsoul.beta.json')

    def read(self):
        keys = [
            ('login', nonEmptyStrJSON, "login"),
            ('password', encodedStrJSON, "password"),
            ('location', nonEmptyStrJSON, "CaptainSoul"),
            ('autoConnect', boolJSON, False),
            ('notification', boolJSON, True),
            ('lastUpdate', intJSON, 0),
            ('mainHeight', intJSON, 500),
            ('mainWidth', intJSON, 350),
            ('chatHeight', intJSON, 200),
            ('chatWidth', intJSON, 200),
            ('downHeight', intJSON, 200),
            ('downWidth', intJSON, 200),
            ('watchlist', nonEmptyStrSetJSON, set())
        ]
        try:
            data = load(file(self._path, 'r'))
            if not isinstance(data, dict):
                logging.error("File is not well formatted")
                data = {}
        except IOError:
            logging.info("File don't exist")
            data = {}
        except ValueError:
            logging.error("File isn't JSON")
            data = {}
        else:
            logging.info("File OK")
        self._data = {key: klass(data.get(key, default)) for key, klass, default in keys}

    def write(self):
        if not os.path.exists(os.path.dirname(self._path)):
            os.makedirs(os.path.dirname(self._path))
        try:
            dump(
                {key: value.toJSON() for key, value in self._data.iteritems()},
                file(self._path, 'w'),
                indent=4,
                separators=(',', ': ')
            )
        except:
            logging.error("Can't write file")
        else:
            logging.info("File successfully written")

    def __getitem__(self, key):
        if key in self._data:
            logging.debug('Get key "%s"' % key)
            return self._data[key].getter()
        else:
            logging.error("Key %s don't exist" % key)
            raise KeyError(key)

    def __setitem__(self, key, value):
        if key in self._data:
            logging.debug('Set key "%s" == "%s"' % (key, value))
            self._data[key].setter(value)
        else:
            logging.error("Key %s don't exist" % key)
            raise KeyError(key)
