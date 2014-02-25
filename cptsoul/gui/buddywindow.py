# coding=utf-8

import random
import string

from PyQt4.QtCore import QAbstractListModel, QSize, QRect, pyqtSlot, QObject, Qt, QModelIndex
from PyQt4.QtGui import QWidget, QHBoxLayout, QListView, QItemDelegate, QStyle, QPixmap, QPainter, QPushButton


class MyDelegate(QItemDelegate):
    def __init__(self, *args, **kwargs):
        super(MyDelegate, self).__init__(*args, **kwargs)
        self.actifImg = QPixmap(":green.png")

    def paint(self, painter, option, idx):
        data = idx.data()
        rect = option.rect
        painter.save()
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        # Background Selected
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        # State
        if data.state == "actif":
            tmpRect = QRect(rect.x() + 5, rect.y() + 5, 20, 20)
            painter.drawPixmap(tmpRect, self.actifImg)
        # Login
        posText = QRect(rect)
        posText.setX(posText.x() + 30)
        painter.drawText(posText, Qt.AlignVCenter, data.login)
        painter.restore()

    def sizeHint(self, option, idx):
        return QSize(100, 30)


class Buddy(QObject):
    def __init__(self, login):
        super(Buddy, self).__init__()
        self.login = login
        self.state = "actif"

    def __gt__(self, other):
        return bool(self.login > other.login)

    def __eq__(self, other):
        return bool(self.login == other.login)


class BuddyList(QAbstractListModel):
    def __init__(self, parent):
        super(BuddyList, self).__init__(parent)
        self._data = {}

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._data)

    def data(self, idx, role=None):
        return sorted(self._data.itervalues())[idx.row()]

    def getBuddyIdx(self, login):
        try:
            return sorted(self._data.iterkeys()).index(login)
        except ValueError:
            return 0

    def addBuddy(self, login):
        if login not in self._data:
            tmp = self._data.keys()
            tmp.append(login)
            idx = sorted(tmp).index(login)
            self.beginInsertRows(QModelIndex(), idx, idx)
            self._data[login] = Buddy(login)
            self.endInsertRows()

    def deleteBuddy(self, login):
        if login in self._data:
            idx = self.getBuddyIdx(login)
            self.beginRemoveRows(QModelIndex(), idx, idx)
            del self._data[login]
            self.endRemoveRows()

    def changeBuddyState(self, login, state):
        if login in self._data:
            idx = self.getBuddyIdx(login)
            self._data[login].state = state
            self.dataChanged.emit(self.createIndex(idx, 0), self.createIndex(idx, 0))


class BuddyWindow(QWidget):
    def __init__(self):
        super(BuddyWindow, self).__init__()
        self.setWindowTitle("CaptainSoul")
        # BuddyList
        self.buddyList = BuddyList(self)
        # Widgets
        self.buddyListView = QListView(self)
        self.buddyListView.setItemDelegate(MyDelegate())
        self.buddyListView.setModel(self.buddyList)
        self.button = QPushButton("Add random", self)
        self.button.clicked.connect(self._handleButtonClicked)
        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.buddyListView)
        layout.addWidget(self.button)
        self.setLayout(layout)

    @pyqtSlot()
    def _handleButtonClicked(self):
        self.buddyList.addBuddy(''.join(random.sample(string.ascii_letters, 8)))