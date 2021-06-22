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

from com.sun.star.lang import XServiceInfo
from com.sun.star.lang import XInitialization
from com.sun.star.mail import XMailServiceSpooler

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from smtpserver import DataSource
from smtpserver import MailSpooler
from smtpserver import TerminateListener

from smtpserver import executeDispatch
from smtpserver import getDesktop
from smtpserver import getMessage
from smtpserver import logMessage
from smtpserver import g_identifier

g_service = 'MailServiceSpooler'

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = 'com.sun.star.mail.%s' % g_service


class MailServiceSpooler(unohelper.Base,
                         XServiceInfo,
                         XMailServiceSpooler):
    def __init__(self, ctx):
        #msg = getMessage(ctx, g_service, 101)
        #logMessage(ctx, INFO, msg, g_service, '__init__()')
        self._ctx = ctx
        self._datasource = DataSource(ctx)
        #msg = getMessage(ctx, g_service, 102)
        #logMessage(ctx, INFO, msg, g_service, '__init__()')
        if self.Spooler is None:
            print("MailServiceSpooler.__init__() 1")
            self._datasource.waitForDataBase()
            print("MailServiceSpooler.__init__() 2")
            spooler = MailSpooler(ctx, self._datasource.DataBase)
            MailServiceSpooler._spooler = spooler
            listener = TerminateListener(spooler)
            getDesktop(ctx).addTerminateListener(listener)

    _spooler = None

    @property
    def Spooler(self):
        return MailServiceSpooler._spooler

    # XMailServiceSpooler
    def start(self):
        self.Spooler.start()

    def stop(self):
        self.Spooler.stop()

    def isStarted(self):
        return self.Spooler.isStarted()

    def addJob(self, sender, subject, document, recipients, attachments):
        try:
            print("MailServiceSpooler.addJob() %s - %s - %s - %s - %s" % (sender, subject, document, recipients, attachments))
            jobid = self._datasource.insertJob(sender, subject, document, recipients, attachments)
            print("MailServiceSpooler.addJob() %s" % jobid)
            return jobid
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    def addMergeJob(self, sender, subject, document, datasource, query, recipients, identifiers, attachments):
        try:
            print("MailServiceSpooler.addMergeJob() %s - %s - %s - %s - %s - %s - %s" % (sender, subject, document, datasource, recipients, identifiers, attachments))
            jobid = self._datasource.insertMergeJob(sender, subject, document, datasource, query, recipients, identifiers, attachments)
            print("MailServiceSpooler.addMergeJob() %s" % jobid)
            return jobid
        except Exception as e:
            msg = "Error: %s" % traceback.print_exc()
            print(msg)

    def removeJob(self, jobid):
        pass
 
    def getJobState(self, jobid):
        pass

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(MailServiceSpooler,                        # UNO object class
                                         g_ImplementationName,                      # Implementation name
                                        (g_ImplementationName,))                    # List of implemented services
