#! /usr/local/bin/python
# -*- coding: utf-8 -*-
# talkw.py

import os
import sys
if __name__ == '__main__':
    sys.path += [os.getcwd() + os.path.sep + '..']

import json

import core
from flask import Flask, render_template, request, redirect

PORT = core.conf.WEBUI_PORT
app = Flask(__name__)


@app.route('/')
def status():
    items = json.loads(core.status())
    return render_template('index.html', items=items)


@app.route('/server', methods=['post'])
def server():
    channel = str(request.form['channel'])
    addr = str(request.form['address'])
    port = int(request.form['port'])
    core.server(channel, (addr, port))
    return redirect('/')


@app.route('/client', methods=['post'])
def client():
    channel = str(request.form['channel'])
    port = int(request.form['port'])
    core.client(channel, port)
    return redirect('/')


@app.route('/kill', methods=['post'])
def kill():
    id_ = int(request.form['id'])
    core.kill(id_)
    return redirect('/')


def run():
    app.run(host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    app.debug = True
    run()
