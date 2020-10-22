#!
# -*- coding: utf_8 -*-

#from __futur__ import absolute_import

import uno
import unohelper

from com.sun.star.util import XCloseListener

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from unolib import getConfiguration
from unolib import createService

from .dbtools import getDataSource

from .database import DataBase
from .dataparser import DataParser

from .configuration import g_identifier

from .logger import logMessage
from .logger import getMessage

from collections import OrderedDict
from threading import Thread
from threading import Condition
import traceback
import time


class DataSource(unohelper.Base,
                 XCloseListener):
    def __init__(self, ctx):
        print("DataSource.__init__() 1")
        self.ctx = ctx
        self._error = None
        self._progress = 0.5
        self._configuration = getConfiguration(self.ctx, g_identifier, False)
        if self._initializeDataBase():
            print("DataSource.__init__() 2")
            self.InitThread = Thread(target=self._initDataBase)
            self.InitThread.start()
        print("DataSource.__init__() 3")

    _DataBase = None
    _InitThread = None

    @property
    def InitThread(self):
        return DataSource._InitThread
    @InitThread.setter
    def InitThread(self, thread):
        DataSource._InitThread = thread
    @property
    def DataBase(self):
        return DataSource._DataBase
    @DataBase.setter
    def DataBase(self, database):
        DataSource._DataBase = database

    def _initializeDataBase(self):
        return self.InitThread is None

    # XRestReplicator
    def cancel(self):
        self.canceled = True
        self.sync.set()
        self.join()

    def loadSmtpConfig(self, email, callback):
        smtpconfig = Thread(target=self._loadSmtpConfig, args=(email, callback))
        smtpconfig.start()

    def _loadSmtpConfig(self, email, callback):
        time.sleep(self._progress)
        callback(10)
        time.sleep(self._progress)
        self.InitThread.join()
        callback(20)
        time.sleep(self._progress)
        domain = self._getDomain(email)
        config = self.DataBase.getSmtpConfig(domain)
        if config is None:
            callback(30)
            self._getIspdbConfig(domain)
        else:
            callback(100)

    def _getIspdbConfig(self, domain):
        url = '%s%s' % (self._configuration.getByName('IspDBUrl'), domain)
        service = 'com.gmail.prrvchr.extensions.OAuth2OOo.OAuth2Service'
        parameter = uno.createUnoStruct('com.sun.star.auth.RestRequestParameter')
        parameter.Method = 'GET'
        parameter.Url = url
        parameter.NoAuth = True
        request = createService(self.ctx, service).getRequest(parameter, DataParser())
        response = request.execute()
        if response.IsPresent:
            print("DataSource._getIspdbConfig() OK")
        else:
            print("DataSource._getIspdbConfig() CANCEL")

    def _getDomain(self, email):
        return email.split('@').pop()

    def _initDataBase(self):
        try:
            msg = "DataSource for Scheme: loading ... "
            print("DataSource.run() 1 *************************************************************")
            self.DataBase = self._getDataBase()
            config = self.DataBase.getSmtpConfig('gmail.com')
            print("DataSource.run() 2 %s" % (config, ))
            print("DataSource.run() 3 *************************************************************")
        except Exception as e:
            msg = "DataSource run(): Error: %s - %s" % (e, traceback.print_exc())
            print(msg)

    def _getDataBase(self):
        database = DataBase(self.ctx, 'SmtpServer')
        database.addCloseListener(self)
        return database

    # XCloseListener
    def queryClosing(self, source, ownership):
        #if self.DataSource.is_alive():
        #    self.DataSource.cancel()
        #    self.DataSource.join()
        #self.deregisterInstance(self.Scheme, self.Plugin)
        #self.DataBase.shutdownDataBase(self.DataSource.fullPull)
        msg = "DataSource queryClosing: Scheme: %s ... Done" % self.Provider.Scheme
        logMessage(self.ctx, INFO, msg, 'DataSource', 'queryClosing()')
        print(msg)
    def notifyClosing(self, source):
        pass
