#!/usr/bin/python
#-*- coding: utf-8 -*-
# PubSubServer.py


from twisted.web          import server, error
from twisted.web.server   import Site
from twisted.web.resource import Resource
from twisted.internet     import reactor, task
from twisted.application  import internet, service

import json
import time

import random
import sys


"""
	publish:
		pubsub.ninilove.com/channelName/publish?message=
		
	subscribe:
		pubsub.ninilove.com/channelName/subscribe?timetoken=
		
	channel list:
		pubsub.ninilove.com/__getInfo/channelList?prefix=
		
"""


class Channel( Resource ):
	isLeaf = True
	
	def __init__( self, channelName ):
		Resource.__init__( self )
		
		self.name = channelName
		self.__lastTimeToken   = None
		self.currentTimeToken() # update lastTimeToken
		
		self.__messages        = []
		self.__delayedRequests = []
		self.lastAccessTime    = time.time()
		
	def currentTimeToken( self ):
		res = float( str( time.time() * 1000 ) )
		if self.__lastTimeToken != None:
			if res <= self.__lastTimeToken:
				res = self.__lastTimeToken + 0.1
		
		self.__lastTimeToken = res
		return res

	def render( self, request ):
		try:
			action = request.postpath[0]
		except IndexError:
			action = None
		
		if action == 'publish':
			return self._publish( request )
		
		elif action == 'subscribe':
			return self._subscribe( request )

		else:
			res = error.NoResource( message="invalid command to channel." )
			return res.render( request )

	def removeOldMessages( self ):
		curTime = time.time()
		tmp = []
		for entry in self.__messages:
			timeToken, message = entry
			sendTime = timeToken / 1000 # 대략적으로 1000 배 이므로.
			if sendTime + 60 < curTime: # 1 분 이상 된 메시지는 지운다.
				tmp.append( entry )
		
		for entry in tmp:
			self.__messages.remove( entry )

	def _publish( self, request ):
		self.lastAccessTime = time.time()

		try:
			messages = request.args[ 'message' ]
		except KeyError:
			messages = None
		
		if messages:
			timeToken = self.currentTimeToken()
			for message in messages:
				obj = json.loads( message )
				self.__messages.append( [ timeToken, obj ] )
		
			self._processDelayedRequests()
			result = [ True, timeToken ]
			return json.dumps( result )
			
		else:
			result = [ False ]
			return json.dumps( result )
		
	def _gatherMessagesAfter( self, timeToken_ ):
		messages = []
		for ( timeToken, message ) in self.__messages:
			if timeToken > timeToken_:
				messages.append( [ timeToken, message ] )
		
		return messages
		
	def _subscribe( self, request ):
		self.lastAccessTime = time.time()
	
		try:
			timeToken = float( request.args[ 'timetoken' ][0] )
		except KeyError:
			timeToken = 0
			
		request.timeToken = timeToken	
			
		if timeToken == 0:
			result = [ True, self.__lastTimeToken ]
			return json.dumps( result )
			
		messages = self._gatherMessagesAfter( timeToken )
		if len( messages ) > 0:
			result = [ True, self.__lastTimeToken, messages ]
			return json.dumps( result )
			
		else:
			self.__delayedRequests.append( request )
			return server.NOT_DONE_YET
		
	def _processDelayedRequests( self ):
		for req in self.__delayedRequests:
			timeToken = req.timeToken
			messages = self._gatherMessagesAfter( timeToken )
			result = [ True, self.__lastTimeToken, messages ]
			
			try:
				req.write( json.dumps( result ) )
				req.finish()
			except: # 커넥션이 사라진 경우임.
				pass

		self.__delayedRequests = []
				


class GetInfo( Resource ):
	isLeaf = True
	
	def __init__( self, server ):
		Resource.__init__( self )
		self.__server = server
		
	def render( self, request ):
		try:
			action = request.postpath[0]
		except IndexError:
			action = None
		
		if action == 'channelList':
			return self._channelList( request )
		
		else:
			res = error.NoResource( message="invalid command to server." )
			return res.render( request )
		
	def _channelList( self, request ):
		try:
			prefix = request.args[ 'prefix' ][0]
		except KeyError:
			prefix = None
					
		res = []
		for channel in self.__server.getChannels():
			if ( None == prefix ) or channel.name.startswith( prefix ):
				res.append( [ channel.name, channel.lastAccessTime ] )
	
		result = [ True, res ]
		return json.dumps( result )



class Server( Resource ):
	isLeaf = False
	
	def __init__( self ):
		Resource.__init__( self )
		
		self.__getInfo  = GetInfo( self )
		self.__channels = {}
		
		loopingCall = task.LoopingCall( self.collectGarbages ) 
		loopingCall.start( 5 * 60, False )
		
	def getChild( self, name, request ):
		# 서버 자체에 대한 API 라면
		if name == '__getInfo':
			return self.__getInfo
	
		# 채널에 대한 요청이라면
		try:
			return self.__channels[ name ]
		
		except KeyError:
			self.__channels[ name ] = Channel( name )
			return self.__channels[ name ]

	def collectGarbages( self ):
		curTime = time.time()
		tmp = []
		for channel in self.__channels.values():
			channel.removeOldMessages()
			if channel.lastAccessTime + 60 * 5 < curTime: # 5 분 동안 억세스가 없었던 채널을 삭제한다.
				tmp.append( channel.name )
				
		for channelName in tmp:
			del self.__channels[ channelName ]			
	
	def getChannels( self ):
		return self.__channels.values()
		
	def getChannelNames( self ):
		return self.__channels.keys()
	
	

# 실행 시, sudo twistd -y ./PubSubServer.py 로 실행할 것.
application = service.Application( 'web' )
site        = Site( Server() )
sc          = service.IServiceCollection( application )
i           = internet.TCPServer( 80, site )
i.setServiceParent( sc )

