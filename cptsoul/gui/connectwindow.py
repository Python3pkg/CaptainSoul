# coding=utf-8

from PyQt4.QtCore import pyqtSignal, pyqtSlot
from PyQt4.QtGui import QWidget, QGridLayout, QLineEdit, QApplication, QLabel, QPushButton, QCheckBox


class ConnectWindow(QWidget):
    successfullyConnected = pyqtSignal()

    def __init__(self):
        super(ConnectWindow, self).__init__()
        config = QApplication.instance().Config
        self.setWindowTitle("CaptainSoul")
        # Widgets
        self._loginEntry = QLineEdit(config["login"], self)
        self._passwdEntry = QLineEdit(config["password"], self)
        self._passwdEntry.setEchoMode(QLineEdit.Password)
        self._button = QPushButton("Connect", self)
        self._button.clicked.connect(self._handleConnectButtonClicked)
        self._autoConnectBox = QCheckBox(self)
        self._autoConnectBox.setChecked(config["autoConnect"])
        self._errorText = QLabel("", self)
        self._errorText.hide()
        # Layout
        layout = QGridLayout(self)
        layout.addWidget(QLabel("Login", self), 0, 0)
        layout.addWidget(self._loginEntry, 0, 1, 1, 2)
        layout.addWidget(QLabel("Password", self), 1, 0)
        layout.addWidget(self._passwdEntry, 1, 1, 1, 2)
        layout.addWidget(QLabel("Auto connect", self), 2, 0)
        layout.addWidget(self._autoConnectBox, 2, 2)
        layout.addWidget(self._errorText, 3, 0, 1, 3)
        layout.addWidget(self._button, 4, 0, 1, 3)
        self.setLayout(layout)
        # Client binding
        client = QApplication.instance().Client
        client.loginFailed.connect(self._handleLoginFailed)
        client.connectionFailed.connect(self._handleConnectionFailed)
        client.connected.connect(self._handleConnect)

    def closeEvent(self, event):
        client = QApplication.instance().Client
        client.loginFailed.disconnect(self._handleLoginFailed)
        client.connectionFailed.disconnect(self._handleConnectionFailed)
        client.connected.disconnect(self._handleConnect)

    @pyqtSlot()
    def _handleConnectButtonClicked(self):
        config = QApplication.instance().Config
        if not self._loginEntry.text() or not self._passwdEntry.text():
            self._errorText.setText("Please enter login and password")
            self._errorText.show()
            return
        config["login"] = str(self._loginEntry.text())
        config["password"] = str(self._passwdEntry.text())
        config["autoConnect"] = self._autoConnectBox.isChecked()
        self._errorText.hide()
        QApplication.instance().Client.connectToHost()

    @pyqtSlot()
    def _handleConnectionFailed(self):
        self._errorText.setText("Connection failed")
        self._errorText.show()

    @pyqtSlot()
    def _handleLoginFailed(self):
        self._errorText.setText("Login failed, check login and password")
        self._errorText.show()

    @pyqtSlot()
    def _handleConnect(self):
        self.successfullyConnected.emit()