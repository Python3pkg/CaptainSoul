# -*- coding: utf-8 -*-

import re
import string


def urlEncode(s):
    r = u''
    if not isinstance(s, unicode):
        s = unicode(s, 'utf8')
    for c in s:
        if c not in string.ascii_letters + string.digits:
            o = ord(c)
            r += (u'%%0%s' if o < 16 else u'%%%s') % hex(o).upper()[2:]
        else:
            r += c
    return r


def urlDecode(s):
    r = u''
    if not isinstance(s, unicode):
        s = unicode(s, 'utf8')
    while s:
        if s[0] == '%':
            try:
                r += unichr(int(s[1:3], 16))
            except ValueError:
                r += '?'
            s = s[3:]
        else:
            r += s[0]
            s = s[1:]
    return r


class Rea(object):
    def __init__(self, regex, f):
        self._regex = re.compile(regex)
        self._f = f

    def try_call(self, entry):
        m = self._regex.match(entry)
        if m is not None and self._f is not None:
            self._f(**m.groupdict())
            return True
        return False

    def try_call_cmd(self, entry, info):
        m = self._regex.match(entry)
        if m is not None and self._f is not None:
            self._f(info, **m.groupdict())
            return True
        return False


class ReaList(object):
    def __init__(self, *args):
        self._reas = [rea for rea in args if isinstance(rea, Rea)]

    def found_match(self, entry):
        for m in self._reas:
            if m.try_call(entry):
                return True
        return False

    def found_match_cmd(self, entry, info):
        for m in self._reas:
            if m.try_call_cmd(entry, info):
                return True
        return False
