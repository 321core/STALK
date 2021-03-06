import json
import os
import socket
import sys

from flask import Flask, render_template, request

if __name__ == '__main__':
    sys.path += [os.getcwd() + os.path.sep + '..']

import core

PORT = core.conf.WEBUI_PORT
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html',
                           hostname=socket.gethostname(),
                           server_address=core.conf.INDEX_SERVER_BASE_URL,
                           id=core.conf.USER_NAME, password=core.conf.PASSWORD,
                           broadcast_port=core.conf.BROADCAST_PORT,
                           web_port=core.conf.WEBUI_PORT)


@app.route('/status')
def status():
    ret = json.loads(core.status())
    return json.dumps({'code': 'success', 'result': ret, 'account': core.conf.USER_NAME})


@app.route('/server', methods=['get'])
def server():
    channel = str(request.args.get('channel'))
    addr = str(request.args.get('address'))
    port = int(request.args.get('port'))
    ret = core.server(channel, (addr, port))
    if ret:
        return json.dumps({'code': 'failure', 'message': ret})

    core.save()
    return json.dumps({'code': 'success'})


@app.route('/client', methods=['get'])
def client():
    channel = str(request.args.get('channel'))

    try:
        port = int(request.args.get('port'))
    except TypeError:
        port = None

    ret = json.loads(core.client(channel, port))
    if isinstance(ret, str):
        return json.dumps({'code': 'failure', 'message': ret})

    core.save()
    return json.dumps({'code': 'success', 'port': ret})


@app.route('/kill', methods=['get'])
def kill():
    id_ = int(request.args.get('id'))
    ret = core.kill(id_)
    if ret:
        return json.dumps({'code': 'failure', 'message': ret})

    core.save()
    return json.dumps({'code': 'success'})


def run():
    app.run(host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    app.debug = True
    run()
