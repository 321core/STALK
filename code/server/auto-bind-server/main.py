# -*- coding: utf-8 -*-
# main.py

import random
import json
import threading
import time
import socket

import requests
from flask import Flask, request


class Entry(object):
    def __init__(self, agent, channel, port):
        assert isinstance(agent, Agent)
        assert isinstance(channel, str)
        assert isinstance(port, int)
        super(Entry, self).__init__()

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
    def __init__(self, hostname, ip_address, port, account):
        assert isinstance(hostname, str)
        assert isinstance(ip_address, str)
        assert isinstance(port, int)
        assert isinstance(account, str)

        super(Agent, self).__init__()
        self.__hostname = hostname
        self.__ip_address = ip_address
        self.__port = port
        self.__account = account
        self.__entries = []
        self.__update_time = time.time()
        self.__status_update_time = 0
        self.update_status()

    @property
    def last_updated_time(self):
        return self.__update_time

    def updated(self):
        self.__update_time = time.time()

    @property
    def status_updated_time(self):
        return self.__status_update_time

    @property
    def hostname(self):
        return self.__hostname

    @property
    def ip_address(self):
        return self.__ip_address

    @property
    def port(self):
        return self.__port

    @property
    def address(self):
        return self.__ip_address, self.__port

    @property
    def account(self):
        return self.__account

    def entries_for_channel(self, channel, port=None):
        assert isinstance(channel, str)

        res = []
        for e in self.__entries:
            if e.channel == channel:
                if port is None or port == e.port:
                    res.append(e)

        return res

    def create_entry(self, channel):
        url = "http://%s:%d/client?channel=%s" % (self.__ip_address, self.__port, channel)
        ret = requests.get(url)
        if ret.ok and ret.json()['code'] == 'success':
            e = Entry(self, channel, ret.json()['port'])
            self.__entries.append(e)
            print 'Entry added - CHANNEL %s AT %s:%d' % (channel, self.__ip_address, e.port)
            return e

    def update_status(self):
        url = "http://%s:%d/status" % (self.__ip_address, self.__port)
        ret = requests.get(url)
        if ret.ok and ret.json()['code'] == 'success':

            old_entries = self.__entries[:]
            new_entries = []

            entries = ret.json()['result']
            for e in entries:
                if e['kind'] == 'client':
                    channel = str(e['channel'])
                    port = e['port']
                    new_entries.append(Entry(self, channel, port))

            self.__entries = new_entries
            self.__status_update_time = time.time()


class BindServer(object):
    def __init__(self):
        super(BindServer, self).__init__()

        self.__agents = []
        self.__lock = threading.Lock()
        self.__detector_thread = None
        self.__sweeper_thread = None
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
                return e.agent.ip_address, e.port

            # create entry
            e = None
            while e is None:
                a = random.choice(agents)
                e = a.create_entry(channel)

            return e.agent.ip_address, e.port

    def start(self):
        assert not self.__detector_thread
        self.__stop = False
        self.__detector_thread = threading.Thread(target=self.__detector)
        self.__detector_thread.start()

        self.__sweeper_thread = threading.Thread(target=self.__sweeper)
        self.__sweeper_thread.start()

    def stop(self):
        assert self.__detector_thread
        self.__stop = True
        self.__detector_thread.join()
        self.__detector_thread = None
        self.__sweeper_thread.join()
        self.__sweeper_thread = None

    def __sweeper(self):
        while not self.__stop:
            cur = time.time()
            with self.__lock:
                agents = self.__agents[:]

            garbages = []
            for a in agents:
                if a.last_updated_time < cur - 10.0:
                    garbages.append(a)
                elif a.status_updated_time < cur - 3.0:
                    a.update_status()

            with self.__lock:
                for a in garbages:
                    self.__agents.remove(a)
                    print 'Agent removed / %s(%s:%d)' % (a.hostname, a.ip_address, a.port)

            time.sleep(1.0)

    def __detector(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 8988))

        while not self.__stop:
            msg, addr = s.recvfrom(4096)

            # parse messsage
            # message = 'STALKAGENT@%s\nWEB_UI:%d\nWEB_SSH:%d\nACCOUNT:%s'
            if msg.startswith('STALKAGENT@'):
                added = []
                port = None
                account = None

                lines = msg.split('\n')
                hostname = lines[0].split('@')[1]
                lines = lines[1:]
                for l in lines:
                    k, v = l.split(':')
                    if k == 'WEB_UI':
                        port = int(v)
                    elif k == 'ACCOUNT':
                        account = v

                if port is not None and account is not None:
                    ip_address, _ = addr
                    a = self.get_agents(account, ip_address, port)
                    if a:
                        for agent in a:
                            agent.updated()

                    else:
                        a = Agent(hostname, ip_address, port, account)
                        added.append(a)

                if added:
                    with self.__lock:
                        self.__agents += added

                    for a in added:
                        print 'Agent detected / %s(%s:%d)' % (hostname, ip_address, port)

            time.sleep(1.0)


app = Flask(__name__)


@app.route('/bind')
def bind():
    account = str(request.args.get('account'))
    channel = str(request.args.get('channel'))
    ret = server.bind(account, channel)
    if ret:
        ip_address, port = ret
        return json.dumps({'code': 'sucess', 'ip_address': ip_address, 'port': port})

    return json.dumps({'code': 'failure'})


if __name__ == '__main__':
    server = BindServer()
    server.start()

    try:
        app.run(host='0.0.0.0', port=8987, debug=True, use_reloader=False)
    finally:
        server.stop()
