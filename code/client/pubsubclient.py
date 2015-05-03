# -*- coding: utf-8 -*-
# pubsubclient.py

import json
import time
import urllib2
import socket
import traceback

import requests


class PubSubClient(object):
    def __init__(self, origin='pubsub.ninilove.com', logger=None):
        super(PubSubClient, self).__init__()

        self.origin = origin
        self.limit = 1800
        self.origin = 'http://' + self.origin
        self.logger = logger

    def _request(self, request, params=None):
        # Build URL
        url = self.origin + '/' + "/".join(request)

        # Send Request Expecting JSONP Response
        try:
            if params:
                ret = requests.post(url, data=params, timeout=60)
            else:
                ret = requests.post(url, timeout=60)

            return ret.json()

        except socket.timeout, e:
            if self.logger:
                self.logger.debug(u"[PubSub] _request 중 타임아웃이 발생하였습니다 리퀘스트:%s" % repr(request))

            return None

        except:
            if self.logger:
                self.logger.error(u"[PubSub] _request 중 에러가 발생하였습니다. 리퀘스트:%s" % repr(request), exc_info=True)

            traceback.print_exc()
            return None


def publish(self, args):
    # Fail if bad input.
    if not (args['channel'] and args['message']):
        return [0, 'Missing Channel or Message']

    # Capture User Input
    channel = str(args['channel'])
    message = json.dumps(args['message'])
    # message = json.dumps(args['message'], separators=(',', ':'))

    # Send Message
    ret = self._request([channel, 'publish'], {'message': '%s' % message})
    if ret:
        return ret

    return [0, "Not Sent", "0"]


def subscribe(self, args):
    # Fail if missing channel
    if not 'channel' in args:
        raise Exception('Missing Channel.')
        return False

    # Fail if missing callback
    if not 'callback' in args:
        raise Exception('Missing Callback.')
        return False

    # Capture User Input
    channel = str(args['channel'])
    callback = args['callback']
    if 'ttcallback' in args:
        ttcallback = args['ttcallback']
    else:
        ttcallback = None

    # Begin Subscribe
    self.continueReceive = True  # modified by CJU, 2013-05-02
    while self.continueReceive:  # modified by CJU, 2013-05-02
        timetoken = 'timetoken' in args and float(args['timetoken']) or 0
        try:
            # # Wait for Message
            response = self._request([channel, 'subscribe'], {'timetoken': "%f" % timetoken})

            # 응답이 없을 때 None 이 반환된다. Exception 이 발생하지 않도록 피해간다.
            if response is None:
                continue

            retCode = response[0]
            args['timetoken'] = response[1]

            # 타임토큰을 얻은 최초의 콜백.
            if ttcallback:
                ttcallback()
                ttcallback = None

            if len(response) >= 3:
                messages = response[2]
            else:
                messages = []

            # If it was a timeout
            if not len(messages):
                if self.logger:
                    self.logger.debug(u"[PubSub] subscribe 에 대한 응답으로 len( messages ) == 0 입니다. 다시 request 합니다.")

                continue

            # Run user Callback and Reconnect if user permits.
            if self.logger:
                self.logger.debug(u"[PubSub] message 가 %d 개 수신되어 콜백을 호출합니다." % len(messages))

            for ( timeToken, message ) in messages:
                if not callback(message):
                    return

        except:
            if self.logger:
                self.logger.error(u"[PubSub] subscribe 중 예외가 발생하였습니다. 1.0 초간 딜레이 후 다시 request 합니다.", exc_info=True)
            else:
                traceback.print_exc()

            time.sleep(1)

    return True
