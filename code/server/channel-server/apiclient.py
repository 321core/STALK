# -*- coding: utf-8 -*-
# apiclient.py

import time
import threading
import urllib
import urllib2

from twisted.internet.defer import setDebugging
from twisted.python import log

import conf

setDebugging(True)

TIMEOUT = 10


class APIClient(object):
    def __init__(self):
        super(APIClient, self).__init__()
        self.__running = False
        self.__queue = []
        self.__lock = threading.Lock()

    @property
    def is_running(self):
        return self.__running

    def start(self):
        assert not self.__running
        th = threading.Thread(target=self.thread_main)
        th.setDaemon(True)
        th.start()
        self.__running = True

    def report_status(self, is_running, num_channels, cpu_rate, memory_rate):
        assert isinstance(is_running, bool)
        assert isinstance(num_channels, int) and 0 <= num_channels
        assert isinstance(cpu_rate, (int, float)) and 0 <= cpu_rate <= 1
        assert isinstance(memory_rate, (int, float)) and 0 <= memory_rate <= 1

        params = {
            'base_url': conf.BASE_URL,
            'is_running': is_running,
            'num_channels': num_channels,
            'cpu_rate': cpu_rate,
            'memory_rate': memory_rate,
            'timestamp': time.time()
        }

        with self.__lock:
            self.__queue.append(params)

    def thread_main(self):
        while True:
            with self.__lock:
                params = self.__queue
                self.__queue = []

            if params:
                for param in params:
                    url = 'http://%s/report_channel_server_status/%s/' % (conf.INDEX_SERVER_BASE_URL, conf.NAME)
                    url += '?' + urllib.urlencode(param)
                    req = urllib2.Request(url)
                    try:
                        urllib2.urlopen(req, timeout=TIMEOUT)

                    except Exception:
                        log.msg(exc=True)

            else:
                time.sleep(0.1)
