# -*- coding: utf-8 -*-

import os

import gtk

from ..SendFile import sendFile
from ..PreparedCaller import PreparedCaller
from tools import sizeFormatter, strRandom

COLUMN_NAME, COLUMN_SIZE, COLUMN_LOGIN, COLUMN_STATE, COLUMN_PROGRESS = range(5)


class UploadList(gtk.TreeView):
    def __init__(self, downmanager, manager):
        super(UploadList, self).__init__(model=gtk.ListStore(str, str, str, str, int))
        self.set_rules_hint(True)
        self._data = {}
        self._fileToSend = {}
        self._manager = manager
        self._downmanager = downmanager
        columns = [
            gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=COLUMN_NAME),
            gtk.TreeViewColumn("Size", gtk.CellRendererText(), text=COLUMN_SIZE),
            gtk.TreeViewColumn("Login", gtk.CellRendererText(), text=COLUMN_LOGIN),
            gtk.TreeViewColumn("State", gtk.CellRendererProgress(), text=COLUMN_STATE, value=COLUMN_PROGRESS),
        ]
        for column in columns:
            self.append_column(column)
        manager.connect('file-start', self.fileStartEvent)

    @property
    def _listStore(self):
        return self.get_model()

    def fileStartEvent(self, widget, info, name, ip, port):
        if (info.login, name) in self._fileToSend:
            path, key = self._fileToSend[(info.login, name)]
            del self._fileToSend[(info.login, name)]
            sendFile(
                path, ip, port,
                PreparedCaller(self.progressCallback, key=key),
                PreparedCaller(self.endCallback, key=key),
                PreparedCaller(self.errorCallback, key=key)
            )

    def startFileTransfer(self, login):
        dialog = gtk.FileChooserDialog(
            title='CatpainSoul - Choose file to upload',
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=('Ok', gtk.RESPONSE_OK, 'Cancel', gtk.RESPONSE_CANCEL)
        )
        if dialog.run() != gtk.RESPONSE_OK:
            dialog.destroy()
        else:
            path = dialog.get_filename()
            dialog.destroy()
            name = os.path.basename(path)
            size = os.stat(path).st_size
            key = strRandom()
            while key in self._data:
                key = strRandom()
            self._fileToSend[(login, name)] = (path, key)
            self._data[key] = self._listStore.append([name, sizeFormatter(size), login, 'Waiting', 0])
            self._manager.sendFileAsk(name, size, ' ', [login])
            self._downmanager.show_all()

    def progressCallback(self, done, total, key):
        if key in self._data:
            self._listStore[self._data[key]][COLUMN_STATE] = 'Uploading'
            self._listStore[self._data[key]][COLUMN_PROGRESS] = (100 * done) / total

    def endCallback(self, key):
        if key in self._data:
            self._listStore[self._data[key]][COLUMN_STATE] = 'Finished'
            self._listStore[self._data[key]][COLUMN_PROGRESS] = 100

    def errorCallback(self, key):
        if key in self._data:
            self._listStore[self._data[key]][COLUMN_STATE] = 'Error'