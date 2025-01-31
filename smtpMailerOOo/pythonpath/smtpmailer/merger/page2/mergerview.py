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

from com.sun.star.view.SelectionType import MULTI

from smtpmailer import createService
from smtpmailer import getContainerWindow
from smtpmailer import logMessage
from smtpmailer import g_extension

from .mergerhandler import Tab1Handler
from .mergerhandler import Tab2Handler
from .mergerhandler import Grid1Handler
from .mergerhandler import Grid2Handler

import traceback


class MergerView(unohelper.Base):
    def __init__(self, ctx, manager, parent, tables, enabled, message):
        self._ctx = ctx
        self._window = getContainerWindow(ctx, parent, None, g_extension, 'MergerPage2')
        rectangle = uno.createUnoStruct('com.sun.star.awt.Rectangle', 0, 5, 285, 195)
        tab1, tab2 = self._getTabPages(manager, 'Tab1', rectangle, 1)
        parent = tab1.getPeer()
        handler = Tab1Handler(manager)
        self._tab1 = getContainerWindow(ctx, parent, handler, g_extension, 'MergerTab1')
        self._tab1.setVisible(True)
        parent = tab2.getPeer()
        handler = Tab2Handler(manager)
        self._tab2 = getContainerWindow(ctx, parent, handler, g_extension, 'MergerTab2')
        self._tab2.setVisible(True)
        self._rectangle = uno.createUnoStruct('com.sun.star.awt.Rectangle', 4, 25, 275, 130)
        self._initTables(tables, enabled)
        self.setMessage(message)

# MergerView getter methods
    def getWindow(self):
        return self._window

    # Table getter methods
    def getTable(self):
        return self._getTable().getSelectedItem()

    # Address getter methods
    def getAddressSort(self):
        state = self._getAddressSort().Model.State
        return not bool(state)

    def getSelectedAddress(self):
        return self._getAddress().getSelectedRows()

    # Recipient getter methods
    def getRecipientSort(self):
        state = self._getRecipientSort().Model.State
        return not bool(state)

    def getSelectedRecipient(self):
        control = self._getRecipient()
        rows = control.getSelectedRows()
        control.deselectAllRows()
        return rows

# MergerView setter methods
    def initGrid1(self, manager):
        data, column = manager.getGridModels(1)
        grid = self._createGrid(self._tab1, data, column, 'Grid1')
        handler = Grid1Handler(manager)
        grid.addSelectionListener(handler)

    def initGrid2(self, manager):
        data, column = manager.getGridModels(2)
        grid = self._createGrid(self._tab2, data, column, 'Grid2')
        handler = Grid2Handler(manager)
        grid.addSelectionListener(handler)

    def setTable(self, table):
        self._getTable().selectItem(table, True)

    def initTables(self, tables, table, enabled):
        control = self._getTable()
        control.Model.StringItemList = tables
        control.selectItem(table, True)
        control.Model.Enabled = enabled

    def _initTables(self, tables, enabled):
        control = self._getTable()
        control.Model.StringItemList = tables
        control.Model.Enabled = enabled

    def initColumn1(self, columns):
        self._getAddressColumn().Model.StringItemList = columns

    def initOrder1(self, columns, orders):
        control = self._getAddressOrder()
        control.Model.StringItemList = columns
        while orders.hasMoreElements():
            column = orders.nextElement()
            index = columns.index(column.Name)
            control.selectItemPos(index, True)

    def initColumn2(self, columns):
        self._getRecipientColumn().Model.StringItemList = columns

    def initOrder2(self, columns, orders):
        control = self._getRecipientOrder()
        control.Model.StringItemList = columns
        while orders.hasMoreElements():
            column = orders.nextElement()
            index = columns.index(column.Name)
            control.selectItemPos(index, True)

    def enableAdd(self, enabled):
        self._getAdd().Model.Enabled = enabled

    def enableRemove(self, enabled):
        self._getRemove().Model.Enabled = enabled

    def enableAddAll(self, enabled):
        self._getAddAll().Model.Enabled = enabled

    def enableRemoveAll(self, enabled):
        self._getRemoveAll().Model.Enabled = enabled

    def setMessage(self, message):
        self._getMessage().Text = message

# MergerView private getter control methods
    def _getTable(self):
        return self._tab1.getControl('ListBox1')

    def _getAddressColumn(self):
        return self._tab1.getControl('ListBox2')

    def _getAddressOrder(self):
        return self._tab1.getControl('ListBox3')

    def _getAddress(self):
        return self._tab1.getControl('Grid1')

    def _getAddAll(self):
        return self._tab1.getControl('CommandButton1')

    def _getAdd(self):
        return self._tab1.getControl('CommandButton2')

    def _getAddressSort(self):
        return self._tab1.getControl('CheckBox1')

    def _getRecipientColumn(self):
        return self._tab2.getControl('ListBox1')

    def _getRecipientOrder(self):
        return self._tab2.getControl('ListBox2')

    def _getRecipient(self):
        return self._tab2.getControl('Grid1')

    def _getRemoveAll(self):
        return self._tab2.getControl('CommandButton1')

    def _getRemove(self):
        return self._tab2.getControl('CommandButton2')

    def _getRecipientSort(self):
        return self._tab2.getControl('CheckBox1')

    def _getMessage(self):
        return self._tab2.getControl('Label1')

# MergerView private methods
    def _getTabPages(self, manager, name, rectangle, i):
        model = self._getTabModel(rectangle)
        self._window.Model.insertByName(name, model)
        tab = self._window.getControl(name)
        tab1 = self._getTabPage(manager, model, tab, 0)
        tab2 = self._getTabPage(manager, model, tab, 1)
        tab.ActiveTabPageID = i
        return tab1, tab2

    def _getTabModel(self, rectangle):
        service = 'com.sun.star.awt.tab.UnoControlTabPageContainerModel'
        model = self._window.Model.createInstance(service)
        model.PositionX = rectangle.X
        model.PositionY = rectangle.Y
        model.Width = rectangle.Width
        model.Height = rectangle.Height
        return model

    def _getTabPage(self, manager, model, tab, i):
        page = model.createTabPage(i +1)
        page.Title = manager.getTabTitle(i +1)
        index = model.getCount()
        model.insertByIndex(index, page)
        return tab.getControls()[i]

    def _createGrid(self, page, data, column, name):
        model = self._getGridModel(page, data, column, name)
        page.Model.insertByName(name, model)
        return page.getControl(name)

    def _getGridModel(self, page, data, column, name):
        service = 'com.sun.star.awt.grid.UnoControlGridModel'
        model = page.Model.createInstance(service)
        model.Name = name
        model.PositionX = self._rectangle.X
        model.PositionY = self._rectangle.Y
        model.Height = self._rectangle.Height
        model.Width = self._rectangle.Width
        model.GridDataModel = data
        model.ColumnModel = column
        model.SelectionModel = MULTI
        model.ShowColumnHeader = True
        #model.ShowRowHeader = True
        model.BackgroundColor = 16777215
        return model
