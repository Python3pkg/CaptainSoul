# coding=utf-8

import hashlib
from collections import deque
from time import time

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt4.QtNetwork import QTcpSocket
from PyQt4.QtGui import QApplication

from cptsoul.protocol.tools import Rea, ReaList, urlDecode, urlEncode


class NsUserCmdInfo(object):
    def __init__(self, no, login, ip, location):
        self.no = int(no)
        self.login = login
        self.ip = ip
        self.location = location


class NsWhoEntry(object):
    def __init__(self, no, login, ip, location, state, res):
        self.no = int(no)
        self.login = login
        self.ip = ip
        self.location = location
        self.state = state
        self.res = res


class NsWhoResult(object):
    def __init__(self, logins):
        self.logins = logins
        self.list = []

    def add(self, entry):
        self.list.append(entry)

    def __iter__(self):
        return iter(self.list)


class NsUserCmd(object):
    def __init__(self, sender):
        self.sender = sender


class NsMsg(NsUserCmd):
    def __init__(self, sender, msg, dests):
        super(NsMsg, self).__init__(sender)
        self.msg = msg
        self.dests = dests


class NsState(NsUserCmd):
    def __init__(self, sender, state):
        super(NsState, self).__init__(sender)
        self.state = state


class NsFileAsk(NsUserCmd):
    def __init__(self, sender, name, size, desc):
        super(NsFileAsk, self).__init__(sender)
        self.name = name
        self.size = size
        self.desc = desc


class NsFileStart(NsUserCmd):
    def __init__(self, sender, name, ip, port):
        super(NsFileStart, self).__init__(sender)
        self.name = name
        self.ip = ip
        self.port = port


class NetsoulClientData(object):
    def __init__(self):
        self.md5 = ""
        self.host = ""
        self.port = ""


class NetsoulClient(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    loginFailed = pyqtSignal()
    connectionFailed = pyqtSignal()
    lineReceived = pyqtSignal(str)
    lineSent = pyqtSignal(str)
    whoReceived = pyqtSignal(NsWhoResult)
    msgReceived = pyqtSignal(NsMsg)
    loginReceived = pyqtSignal(NsUserCmd)
    logoutReceived = pyqtSignal(NsUserCmd)
    stateReceived = pyqtSignal(NsState)
    isTypingReceived = pyqtSignal(NsUserCmd)
    cancelTypingReceived = pyqtSignal(NsUserCmd)
    fileAskReceived = pyqtSignal(NsFileAsk)
    fileStartReceived = pyqtSignal(NsFileStart)
    NETSOUL_HOST = "ns-server.epita.fr"
    NETSOUL_PORT = 4242

    def __init__(self):
        super(NetsoulClient, self).__init__()
        # Socket
        self._sock = QTcpSocket(self)
        self._sock.connected.connect(self._sockConnected)
        self._sock.disconnected.connect(self._sockDisconnected)
        self._sock.readyRead.connect(self._sockReadyRead)
        self._sock.error.connect(self._sockError)
        # Data
        self._info = NetsoulClientData()
        self._responseQueue = deque()
        self._whoQueue = deque()
        self._logged = False
        self._realist = ReaList(
            Rea(r"^rep (?P<no>\d+) -- .*$", self._responseHook),
            Rea(r"^ping (?P<t>\d+)\s?$", self._pingHook),
            Rea(r"^salut (?P<num>\d+) (?P<md5_hash>[0-9a-fA-F]{32}) (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r" (?P<port>\d{1,5}) (?P<timestamp>\d+)$", self._salutHook),
            Rea(r"^user_cmd (?P<no>\d+):\w+:\d+/\d+:(?P<login>.+)@(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                r":.+:(?P<loc>.+):.+ \| (?P<cmd>.*)$", self._userCmdHook))
        self._cmdRealist = ReaList(
            Rea(r"^who (?P<no>\d+) (?P<login>.+) (?P<ip>[\d\.]{7,15}) \d+ \d+ \d+ \d+ .+ (?P<loc>.+)"
                r" .+ (?P<state>\w+)(:\d+)? (?P<res>.+)$", self._cmdWhoHook),
            Rea(r"^who rep 002 -- cmd end$", self._cmdWhoEndHook),
            Rea(r"^msg (?P<msg>.+) dst=(?P<dest>.*)$", self._cmdMsgHook),
            Rea(r"^state (?P<state>\w+?)(:\d+)?\s?$", self._cmdStateHook),
            Rea(r"^login\s?$", self._cmdLoginHook),
            Rea(r"^logout\s?$", self._cmdLogoutHook),
            Rea(r"^dotnetSoul_UserTyping null dst=.*$", self._cmdIsTypingHook),
            Rea(r"^dotnetSoul_UserCancelledTyping null dst=.*$", self._cmdCancelTypingHook),
            Rea(r"^file_ask (?P<data>.+) dst=.*$", self._cmdFileAskHook),
            Rea(r"^file_start (?P<data>.+) dst=.*$", self._cmdFileStartHook)
        )

    def isConnected(self):
        return bool(self._sock.state() == QTcpSocket.ConnectedState)

    def connectToHost(self):
        if self._sock.state() == QTcpSocket.ConnectedState:
            self.close()
        self._sock.connectToHost(self.NETSOUL_HOST, self.NETSOUL_PORT)

    def close(self):
        self._sock.close()

    def sendLine(self, line):
        if self._sock.state() == QTcpSocket.ConnectedState:
            self._sock.write(line + "\n")
            self.lineSent.emit(line)

    @pyqtSlot()
    def _sockConnected(self):
        self._info = NetsoulClientData()
        self._responseQueue = deque()
        self._whoQueue = deque()
        self._logged = False

    @pyqtSlot()
    def _sockDisconnected(self):
        self.close()
        if self._logged:
            self.disconnected.emit()
            self._logged = False

    @pyqtSlot(QTcpSocket.SocketError)
    def _sockError(self, error):
        if error == QTcpSocket.SocketTimeoutError and not self._logged:
            self.connectionFailed.emit()
        elif error == QTcpSocket.ConnectionRefusedError:
            self.connectionFailed.emit()
        elif error == QTcpSocket.RemoteHostClosedError and not self._logged:
            self.connectionFailed.emit()
        else:
            pass
        self._sock.close()

    @pyqtSlot()
    def _sockReadyRead(self):
        if self._sock.canReadLine():
            line = str(self._sock.readLine()).strip()
            if line:
                self.lineReceived.emit(line)
                if not self._realist.found_match(line):
                    pass

    # HOOKS

    def _userCmdHook(self, no, login, ip, loc, cmd):
        self._cmdRealist.found_match_cmd(cmd, NsUserCmdInfo(int(no), login, ip, loc))

    def _responseHook(self, no):
        if self._responseQueue:
            self._responseQueue.popleft()(int(no))

    def _pingHook(self, t):
        self.sendLine('ping %s' % t)

    def _salutHook(self, num, md5_hash, ip, port, timestamp):
        self._info.md5 = md5_hash
        self._info.host = ip
        self._info.port = port
        self.sendLine('auth_ag ext_user none none')
        self._responseQueue.append(self._responseSalutHook)

    # CMD HOOKS

    def _cmdWhoHook(self, info, no, login, ip, loc, state, res):
        if self._whoQueue:
            self._whoQueue[0].add(NsWhoEntry(no, login, ip, loc, state, res))

    def _cmdWhoEndHook(self, info):
        if self._whoQueue:
            self.whoReceived.emit(self._whoQueue.popleft())

    def _cmdMsgHook(self, info, msg, dest):
        self.msgReceived.emit(NsMsg(info, urlDecode(msg), dest.split(',')))

    def _cmdLoginHook(self, info):
        self.loginReceived.emit(info)

    def _cmdLogoutHook(self, info):
        self.logoutReceived.emit(info)

    def _cmdStateHook(self, info, state):
        self.stateReceived.emit(info, state)

    def _cmdIsTypingHook(self, info):
        self.isTypingReceived.emit(info)

    def _cmdCancelTypingHook(self, info):
        self.cancelTypingReceived.emit(info)

    def _cmdFileAskHook(self, info, data):
        name, size, desc, pas = urlDecode(data).split(' ', 4)
        self.fileAskReceived.emit(NsFileAsk(info, urlDecode(name), int(size), urlDecode(desc)))

    def _cmdFileStartHook(self, info, data):
        name, ip, port = urlDecode(data).split(' ', 3)
        self.fileStartReceived.emit(NsFileStart(info, urlDecode(name), urlDecode(ip), int(port)))

    # RESPONSE HOOKS

    def _responseSalutHook(self, no):
        if no == 2:
            config = QApplication.instance().Config
            md5_hash = hashlib.md5('%s-%s/%s%s' % (
                self._info.md5, self._info.host, self._info.port, config['password'])).hexdigest()
            self.sendLine('ext_user_log %s %s %s %s' % (
                config['login'], md5_hash, urlEncode(config['location']), 'CaptainSoul'))
            self._responseQueue.append(self._responseLogHook)

    def _responseLogHook(self, no):
        if no == 2:
            self._logged = True
            self.connected.emit()
            self.sendWatch()
        elif no == 33:
            self.loginFailed.emit()
        elif no == 131:
            # permission denied
            self.loginFailed.emit()
        else:
            self.loginFailed.emit()

    # COMMANDS

    def sendState(self, state):
        if state:
            self.sendLine('state %s:%d' % (state, time()))

    def sendWatch(self, sendWho=True):
        config = QApplication.instance().Config
        self.sendLine('user_cmd watch_log_user {%s}' % ','.join(config['watchlist']))
        if sendWho:
            self.sendWho(config['watchlist'])

    def sendWho(self, logins):
        if logins:
            self._whoQueue.append(NsWhoResult(logins))
            self.sendLine('user_cmd who {%s}' % ','.join(logins))

    def sendExit(self):
        self.sendLine('exit')

    def sendCmdUser(self, cmd, data, dests):
        if cmd and data and dests:
            self.sendLine('user_cmd msg_user {%s} %s %s' % (','.join(dests), cmd, urlEncode(data)))

    def sendMsg(self, msg, dests):
        self.sendCmdUser('msg', msg, dests)

    def sendStartTyping(self, dests):
        self.sendCmdUser('dotnetSoul_UserTyping', 'null', dests)

    def sendCancelTyping(self, dests):
        self.sendCmdUser('dotnetSoul_UserCancelledTyping', 'null', dests)

    def sendFileAsk(self, name, size, desc, dests):
        self.sendCmdUser('file_ask', '%s %d %s passive' % (urlEncode(name), size, urlEncode(desc)), dests)

    def sendFileStart(self, name, ip, port, dests):
        self.sendCmdUser('file_start', '%s %s %d' % (urlEncode(name), ip, port), dests)