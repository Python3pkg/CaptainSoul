# -*- coding: utf-8 -*-

from twisted.internet.protocol import ServerFactory

from Protocol import GetFileProtocol


class GetFileFactory(ServerFactory):
    def __init__(self, coCall, proCall, endCall):
        self._coCall, self._proCall, self._endCall = coCall, proCall, endCall

    def buildProtocol(self, addr):
        return GetFileProtocol(self._coCall, self._proCall, self._endCall)