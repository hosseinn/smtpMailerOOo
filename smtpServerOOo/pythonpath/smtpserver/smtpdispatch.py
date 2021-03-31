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

from com.sun.star.frame import XNotifyingDispatch

from com.sun.star.frame.DispatchResultState import SUCCESS
from com.sun.star.frame.DispatchResultState import FAILURE

from com.sun.star.ui.dialogs.ExecutableDialogResults import OK

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from smtpserver import DataSource
from smtpserver import Wizard

from smtpserver import getMessage
from smtpserver import getPathSettings
from smtpserver import logMessage
from smtpserver import g_extension
from smtpserver import g_identifier
from smtpserver import g_ispdb_page
from smtpserver import g_ispdb_paths
from smtpserver import g_merger_page
from smtpserver import g_merger_paths

from .ispdb import IspdbWizard
from .merger import MergerWizard
from .sender import SenderManager
from .spooler import SpoolerManager

import traceback


class SmtpDispatch(unohelper.Base,
                   XNotifyingDispatch):
    def __init__(self, ctx, parent):
        self._ctx = ctx
        self._parent = parent
        self._listeners = []
        print("SmtpDispatch.__init__()")

    _datasource = None

    @property
    def DataSource(self):
        return SmtpDispatch._datasource

# XNotifyingDispatch
    def dispatchWithNotification(self, url, arguments, listener):
        print("SmtpDispatch.dispatchWithNotification() 1")
        state, result = self.dispatch(url, arguments)
        struct = 'com.sun.star.frame.DispatchResultEvent'
        notification = uno.createUnoStruct(struct, self, state, result)
        print("SmtpDispatch.dispatchWithNotification() 2")
        listener.dispatchFinished(notification)
        print("SmtpDispatch.dispatchWithNotification() 3")

    def dispatch(self, url, arguments):
        print("SmtpDispatch.dispatch() 1")
        if self.DataSource is None:
            SmtpDispatch._datasource = DataSource(self._ctx)
        state = SUCCESS
        result = None
        if url.Path == 'ispdb':
            state, result = self._showIspdb()
        elif url.Path == 'spooler':
            self._showSpooler()
        elif url.Path == 'mailer':
            state, result = self._showMailer(arguments)
        elif url.Path == 'merger':
            self._showMerger()
        return state, result
        print("SmtpDispatch.dispatch() 2")

    def addStatusListener(self, listener, url):
        pass

    def removeStatusListener(self, listener, url):
        pass

# SmtpDispatch private methods
    #Server methods
    def _showIspdb(self):
        try:
            print("_showIspdb()")
            state = FAILURE
            email = None
            msg = "Wizard Loading ..."
            wizard = Wizard(self._ctx, g_ispdb_page, True, self._parent)
            controller = IspdbWizard(self._ctx, wizard, self.DataSource)
            arguments = (g_ispdb_paths, controller)
            wizard.initialize(arguments)
            msg += " Done ..."
            if wizard.execute() == OK:
                state = SUCCESS
                email = controller.Model.Email
                msg +=  " Retrieving SMTP configuration OK..."
            controller.dispose()
            print(msg)
            logMessage(self._ctx, INFO, msg, 'SmtpDispatch', '_showIspdb()')
            return state, email
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    #Spooler methods
    def _showSpooler(self):
        try:
            print("SmtpDispatch._showSpooler() 1")
            manager = SpoolerManager(self._ctx, self.DataSource, self._parent)
            if manager.execute() == OK:
                print("SmtpDispatch._showSpooler() 2")
            manager.dispose()
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    #Mailer methods
    def _showMailer(self, arguments):
        try:
            state = FAILURE
            for argument in arguments:
                if argument.Name == 'Path':
                    path = argument.Value
                    break
            else:
                path = getPathSettings(self._ctx).Work
            sender = SenderManager(self._ctx, path)
            url = sender.getDocumentUrl()
            if url is not None:
                if sender.showDialog(self.DataSource, self._parent, url) == OK:
                    state = SUCCESS
                    path = sender.Mailer.Model.Path
                sender.dispose()
            return state, path
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    #Merger methods
    def _showMerger(self):
        try:
            print("_showMerger()")
            msg = "Wizard Loading ..."
            wizard = Wizard(self._ctx, g_merger_page, True, self._parent)
            controller = MergerWizard(self._ctx, wizard, self.DataSource)
            arguments = (g_merger_paths, controller)
            wizard.initialize(arguments)
            msg += " Done ..."
            if wizard.execute() == OK:
                msg +=  " Merging SMTP email OK..."
            controller.dispose()
            print(msg)
            logMessage(self._ctx, INFO, msg, 'SmtpDispatch', '_showMerger()')
        except Exception as e:
            msg = "Error: %s - %s" % (e, traceback.print_exc())
            print(msg)
