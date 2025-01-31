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

from com.sun.star.util import XCloseListener
from com.sun.star.datatransfer import XTransferable

from com.sun.star.uno import Exception as UnoException

from com.sun.star.mail.MailServiceType import SMTP

from com.sun.star.ucb.ConnectionMode import OFFLINE

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from smtpmailer import MailTransferable
from smtpmailer import createService
from smtpmailer import getConnectionMode
from smtpmailer import getMail
from smtpmailer import getMessage
from smtpmailer import getUrl
from smtpmailer import logMessage
from smtpmailer import setDebugMode

from .database import DataBase

from .dbtool import Array

from .dataparser import DataParser

from threading import Thread
import traceback
import time


class DataSource(unohelper.Base,
                 XCloseListener):
    def __init__(self, ctx):
        print("DataSource.__init__() 1")
        self._ctx = ctx
        self._dbname = 'SmtpMailer'
        if not self._isInitialized():
            print("DataSource.__init__() 2")
            DataSource._init = Thread(target=self._initDataBase)
            DataSource._init.start()
        print("DataSource.__init__() 3")

    _init = None
    _database = None

    @property
    def DataBase(self):
        return DataSource._database

    def dispose(self):
        self.waitForDataBase()
        self.DataBase.dispose()

    # XCloseListener
    def queryClosing(self, source, ownership):
        self.DataBase.shutdownDataBase()
        msg = "DataBase  '%s' closing ... Done" % self._dbname
        logMessage(self._ctx, INFO, msg, 'DataSource', 'queryClosing()')
        print(msg)
    def notifyClosing(self, source):
        pass

# Procedures called by Ispdb
    def saveUser(self, *args):
        self.DataBase.mergeUser(*args)

    def saveServer(self, new, provider, host, port, server):
        if new:
            self.DataBase.mergeProvider(provider)
            self.DataBase.mergeServer(provider, server)
        else:
            self.DataBase.updateServer(host, port, server)

    def waitForDataBase(self):
        DataSource._init.join()

    def getSmtpConfig(self, *args):
        Thread(target=self._getSmtpConfig, args=args).start()

    def smtpConnect(self, *args):
        setDebugMode(self._ctx, True)
        Thread(target=self._smtpConnect, args=args).start()

    def smtpSend(self, *args):
        setDebugMode(self._ctx, True)
        Thread(target=self._smtpSend, args=args).start()

# Procedures called by the Mailer
    def getSenders(self, *args):
        Thread(target=self._getSenders, args=args).start()

    def removeSender(self, sender):
        return self.DataBase.deleteUser(sender)

# Procedures called by the SpoolerService
    def insertJob(self, sender, subject, document, recipient, attachment):
        recipients = Array('VARCHAR', recipient)
        attachments = Array('VARCHAR', attachment)
        id = self.DataBase.insertJob(sender, subject, document, recipients, attachments)
        return id

    def insertMergeJob(self, sender, subject, document, datasource, query, table, identifier, bookmark, recipient, index, attachment):
        recipients = Array('VARCHAR', recipient)
        indexes = Array('VARCHAR', index)
        attachments = Array('VARCHAR', attachment)
        id = self.DataBase.insertMergeJob(sender, subject, document, datasource, query, table, identifier, bookmark, recipients, indexes, attachments)
        return id

    def deleteJob(self, job):
        jobs = Array('INTEGER', job)
        return self.DataBase.deleteJob(jobs)

    def getJobState(self, job):
        return self.DataBase.getJobState(job)

    def getJobIds(self, batch):
        return self.DataBase.getJobIds(batch)

# Procedures called internally by Ispdb
    def _getSmtpConfig(self, email, url, progress, updateModel):
        progress(5)
        url = getUrl(self._ctx, url)
        progress(10)
        mode = getConnectionMode(self._ctx, url.Server)
        progress(20)
        self.waitForDataBase()
        progress(40)
        user, servers = self.DataBase.getSmtpConfig(email)
        if len(servers) > 0:
            progress(100, 1)
        elif mode == OFFLINE:
            progress(100, 2)
        else:
            progress(60)
            service = 'com.gmail.prrvchr.extensions.OAuth2OOo.OAuth2Service'
            request = createService(self._ctx, service)
            response = self._getIspdbConfig(request, url.Complete, user.getValue('Domain'))
            if response.IsPresent:
                progress(80)
                servers = self.DataBase.setSmtpConfig(response.Value)
                progress(100, 3)
            else:
                progress(100, 4)
        updateModel(user, servers, mode)

    def _getIspdbConfig(self, request, url, domain):
        parameter = uno.createUnoStruct('com.sun.star.auth.RestRequestParameter')
        parameter.Method = 'GET'
        parameter.Url = '%s%s' % (url, domain)
        parameter.NoAuth = True
        #parameter.NoVerify = True
        response = request.getRequest(parameter, DataParser()).execute()
        return response

    def _smtpConnect(self, context, authenticator, progress, callback):
        progress(0)
        step = 2
        progress(5)
        service = 'com.sun.star.mail.MailServiceProvider2'
        progress(25)
        server = createService(self._ctx, service).create(SMTP)
        progress(50)
        try:
            server.connect(context, authenticator)
        except UnoException as e:
            progress(100)
        else:
            progress(75)
            if server.isConnected():
                server.disconnect()
                step = 4
                progress(100)
            else:
                progress(100)
        setDebugMode(self._ctx, False)
        callback(step)

    def _smtpSend(self, context, authenticator, sender, recipient, subject, message, progress, setStep):
        step = 3
        progress(5)
        service = 'com.sun.star.mail.MailServiceProvider2'
        progress(25)
        server = createService(self._ctx, service).create(SMTP)
        progress(50)
        try:
            server.connect(context, authenticator)
        except UnoException as e:
            print("DataSoure._smtpSend() 1 Error: %s" % e.Message)
        else:
            progress(75)
            if server.isConnected():
                body = MailTransferable(self._ctx, message, False)
                mail = getMail(self._ctx, sender, recipient, subject, body)
                print("DataSoure._smtpSend() 2: %s - %s" % (type(mail), mail))
                try:
                    server.sendMailMessage(mail)
                except UnoException as e:
                    print("DataSoure._smtpSend() 3 Error: %s - %s" % (e.Message, traceback.print_exc()))
                else:
                    step = 5
                server.disconnect()
        progress(100)
        setDebugMode(self._ctx, False)
        setStep(step)

# Procedures called internally by the Mailer
    def _getSenders(self, callback):
        self.waitForDataBase()
        senders = self.DataBase.getSenders()
        callback(senders)

# Procedures called internally by the Spooler
    def _initSpooler(self, callback):
        self.waitForDataBase()
        callback()

# Private methods
    def _isInitialized(self):
        return DataSource._init is not None

    def _initDataBase(self):
        time.sleep(0.5)
        database = DataBase(self._ctx, self._dbname)
        DataSource._database = database
