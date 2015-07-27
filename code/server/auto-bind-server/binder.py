# -*- coding: utf-8 -*-
# binder.py

import socket
import random
import json
import threading
import time

import requests


class Entry(object):
    def __init__(self, agent, channel, port):
        assert isinstance(agent, Agent)
        assert isinstance(channel, str)
        assert isinstance(port, int)
        super(Entry, object).__init__()

        self.__agent = agent
        self.__channel = channel
        self.__port = port

    @property
    def agent(self):
        return self.__agent

    @property
    def channel(self):
        return self.__channel

    @property
    def port(self):
        return self.__port


class Agent(object):
    def __init__(self, ip_address, port, account):
        assert isinstance(ip_address, str)
        assert isinstance(port, int)
        assert isinstance(account, str)

        super(Agent, self).__init__()
        self.__ip_address = ip_address
        self.__port = port
        self.__account = account
        self.__entries = []

    @property
    def address(self):
        return self.__ip_address, self.__port

    @property
    def account(self):
        return self.__account

    def entries_for_channel(self, channel):
        assert isinstance(channel, str)

        res = []
        for e in self.__entries:
            if e.channel == channel:
                res.append(e)

        return res

    def create_entry(self, channel):
        url = "http://%s:%d/client?channel=%s" % (self.__ip_address, self.__port, channel)
        ret = requests.get(url)
        if ret.ok and ret.json()['code'] == 'success':
            e = Entry(self, channel, ret.json()['port'])
            self.__entries.append(e)
            return e


class BindServer(object):
    def __init__(self):
        super(BindServer, self).__init__()

        self.__agents = []
        self.__lock = threading.Lock()
        self.__thread = None
        self.__stop = False

    def agents_for_account(self, account):
        res = []
        for a in self.__agents:
            if a.account == account:
                res.append(a)

        return res

    def get_agents(self, account, ip_address, port):
        res = []
        for a in self.__agents:
            if a.account == account and a.ip_address == ip_address and a.port == port:
                res.append(a)

        return res

    def bind(self, account, channel):
        agents = self.agents_for_account(account)
        if agents:
            entries = []
            for a in agents:
                entries += a.entries_for_channel(channel)

            if entries:
                e = random.choice(entries)
                return e.ip_address, e.port

            # create entry
            e = None
            while e is None:
                a = random.choice(agents)
                e = a.create_entry()

            return e.ip_address, e.port

    def start(self):
        assert not self.__thread
        self.__stop = False
        self.__thread = threading.Thread(target=self.__detector)
        self.__thread.start()

    def stop(self):
        assert self.__thread
        self.__stop = True
        self.__thread.join()
        self.__thread = None

    def __detector(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', 8988))

        while not self.__stop:
            msg, addr = s.recvfrom(4096)

            # parse messsage
            # message = 'STALKAGENT@%s\nWEB_UI:%d\nWEB_SSH:%d\nACCOUNT:%s'
            if msg.startswith('STALKAGENT@'):
                added = []
                port = None
                account = None

                lines = msg.split('\n')[1:]
                for l in lines:
                    k, v = l.split(':')
                    if k == 'WEB_UI':
                        port = int(v)
                    elif k == 'ACCOUNT':
                        account = v

                if port is not None and account is not None:
                    ip_address, _ = addr
                    a = self.get_agents(account, ip_address, port)
                    if not a:
                        a = Agent(ip_address, port, account)
                        added.append(a)

                print added ##

                if added:
                    with self.__lock:
                        self.__agents += added

                    print 'Agents', self.__agents

            time.sleep(1.0)


if __name__ == '__main__':
    #
    server = BindServer()
    server.start()

    #
    from flask import Flask, request

    app = Flask(__file__)

    @app.route('/bind')
    def bind():
        account = request.args.get('account')
        channel = request.args.get('channel')
        ret = server.bind(account, channel)
        if ret:
            ip_address, port = ret
            return json.dumps({'code': 'sucess', 'ip_address': ip_address, 'port': port})

        return json.dumps({'code': 'failure'})

    try:
        app.run(host='0.0.0.0', port=8987)
    finally:
        server.stop()
