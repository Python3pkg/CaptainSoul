# coding=utf-8

import sys

from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QApplication, QIcon, QPixmap

from cptsoul.config import ConfigFile
from cptsoul.protocol.netsoul import NetsoulClient
from cptsoul.gui.connectwindow import ConnectWindow
from cptsoul.gui.buddywindow import BuddyWindow, MyDelegate


class CptsoulApp(QApplication):
    def __init__(self):
        super(CptsoulApp, self).__init__(sys.argv)
        # Defaults
        self.setWindowIcon(QIcon(":shield.png"))
        self.setApplicationName("CaptainSoul")
        self.setOrganizationName("Gosselin Jean-Baptiste")
        self.setOrganizationDomain("http://dennajort.fr")
        # ConfigFile
        self.Config = ConfigFile()
        self.aboutToQuit.connect(self.Config.write)
        # NetsoulClient
        self.Client = NetsoulClient()
        self.Client.lineReceived.connect(self._handleClientLineReceived)
        self.Client.lineSent.connect(self._handleClientLineSent)
        # ConnectWindow
        self.connectWindow = ConnectWindow()
        self.connectWindow.successfullyConnected.connect(self._handleSucessfullyConnected)
        self.connectWindow.show()
        # BuddyWindow
        self.buddyWindow = None

    @pyqtSlot(str)
    def _handleClientLineReceived(self, line):
        print "<< %s" % line

    @pyqtSlot(str)
    def _handleClientLineSent(self, line):
        print ">> %s" % line

    @pyqtSlot()
    def _handleSucessfullyConnected(self):
        self.connectWindow.close()
        self.buddyWindow = BuddyWindow()
        self.buddyWindow.show()
        self.connectWindow.successfullyConnected.disconnect(self._handleSucessfullyConnected)
        self.connectWindow.destroy()