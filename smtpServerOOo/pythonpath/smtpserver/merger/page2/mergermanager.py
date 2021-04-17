#!
# -*- coding: utf_8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

import uno
import unohelper

from com.sun.star.ui.dialogs import XWizardPage

from com.sun.star.ui.dialogs.WizardTravelType import FORWARD
from com.sun.star.ui.dialogs.WizardTravelType import BACKWARD
from com.sun.star.ui.dialogs.WizardTravelType import FINISH

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from smtpserver import getMessage
from smtpserver import logMessage

from .mergerview import MergerView
from .mergerhandler import AddressHandler
from .mergerhandler import RecipientHandler

import traceback


class MergerManager(unohelper.Base,
                    XWizardPage):
    def __init__(self, ctx, wizard, model, pageid, parent):
        self._ctx = ctx
        self._wizard = wizard
        self._model = model
        self._pageid = pageid
        self._disabled = False
        tables = self._model.getFilteredTables()
        self._view = MergerView(ctx, self, parent, tables)
        print("mergerManager.__init__() 1")
        address = AddressHandler(self)
        recipient = RecipientHandler(self)
        print("mergerManager.__init__() 2")
        self._model.initRowSet(address, recipient, self.initTab1, self.initTab2)
        print("mergerManager.__init__() 3")
        # TODO: We must disable the handler "ChangeAddressBook" otherwise it activates twice
        self._disableHandler()
        print("mergerManager.__init__() 4")
        self._view.setTable()
        print("mergerManager.__init__() 5")

    @property
    def Model(self):
        return self._model

    # TODO: One shot disabler handler
    def isHandlerEnabled(self):
        enabled = True
        if self._disabled:
            self._disabled = enabled = False
        return enabled
    def _disableHandler(self):
        self._disabled = True

# XWizardPage
    @property
    def PageId(self):
        return self._pageid
    @property
    def Window(self):
        return self._view.getWindow()

    def activatePage(self):
        if self._model.isChanged():
            print("MergerManager.activatePage() 1")
            self._model.updateColumn2(self.updateColumn2)
            print("MergerManager.activatePage() 2")
        if self._model.isFiltered():
            print("MergerManager.activatePage() 3")
            tables = self._model.getFilteredTables()
            print("MergerManager.activatePage() 4")
            # TODO: We must disable the handler "ChangeAddressTable" otherwise it activates twice
            print("MergerManager.activatePage() 5")
            self._disableHandler()
            print("MergerManager.activatePage() 6")
            self._view.initTable(tables)
            print("MergerManager.activatePage() 7")
        print("MergerManager.activatePage() 8")

    def commitPage(self, reason):
        return True

    def canAdvance(self):
        print("MergerManager2.canAdvance() 1")
        advance = self._model.getRecipientCount() > 0
        print("MergerManager2.canAdvance() 2 %s" % advance)
        return advance

# MergerManager setter methods
    def updateColumn2(self, columns, orders):
        print("MergerManager.updateColumn2() 1")
        self._view.updateColumn2(columns, orders)

    def setAddressTable(self, table):
        print("MergerManager.setAddressTable() ************************")
        self._model.setAddressTable(table)

    def recipientChanged(self, enabled):
        self._model.recipientChanged()
        self._view.enableRemoveAll(enabled)
        message = self._model.getMailingMessage()
        self._view.setMessage(message)
        self._wizard.updateTravelUI()

    def addressChanged(self, enabled):
        self._model.addressChanged()
        self._view.enableAddAll(enabled)

    def initTab1(self, columns, orders):
        self._view.updateColumn1(columns, orders)

    def initTab2(self, columns, orders, message):
        self._view.updateColumn2(columns, orders)
        self._view.setMessage(message)



    def setAddressColumn(self, titles, reset):
        self._model.setAddressColumn(titles, reset)

    def setAddressOrder(self, titles):
        ascending = self._view.getAddressSort()
        self._model.setAddressOrder(titles, ascending)

    def setRecipientColumn(self, titles, reset):
        self._model.setRecipientColumn(titles, reset)

    def setRecipientOrder(self, titles):
        ascending = self._view.getRecipientSort()
        self._model.setRecipientOrder(titles, ascending)

    def changeAddress(self, selected):
        self._view.enableAdd(selected)

    def changeRecipient(self, selected, index):
        self._view.enableRemove(selected)
        if selected:
            self._model.setDocumentRecord(index +1)

    def addItem(self):
        rows = self._view.getSelectedAddress()
        self._model.addItem(rows)

    def addAllItem(self):
        rows = range(self._model.getAddressCount())
        self._model.addItem(rows)

    def removeItem(self):
        rows = self._view.getSelectedRecipient()
        self._model.removeItem(rows)

    def removeAllItem(self):
        rows = range(self._model.getRecipientCount())
        self._model.removeItem(rows)
