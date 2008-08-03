##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: rpc.py 4698 2006-11-27 12:30:44Z ced $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from PyQt4.QtCore import *
import xmlrpclib
import logging
import socket
import tiny_socket
from common import notifier
import traceback
import copy

class RpcException(Exception):
	def __init__(self, code, backtrace):

		self.code = code
		self.args = backtrace
		if hasattr(code, 'split'):
			lines = code.split('\n')
	
			self.type = lines[0].split(' -- ')[0]
			self.message = ''
			if len(lines[0].split(' -- ')) > 1:
				self.message = lines[0].split(' -- ')[1]
	
			self.data = '\n'.join(lines[2:])
		else:
			self.type = 'error'
			self.message = backtrace
			self.data = backtrace

		self.backtrace = backtrace

## @brief The Connection class provides an abstract interface for a RPC
# protocol
class Connection:
	def __init__(self):
		self.authorized = False

	def connect(self, database, uid, password):
		self.databaseName = database
		self.uid = uid
		self.password = password

	def call(self, url, method, *args ):
		pass

## @brief The SocketConnection class implements Connection for the TinyERP socket RPC protocol.
#
# The socket RPC protocol is usually opened at port 8070 on the server.
class SocketConnection(Connection):
	def convert(self, result): 
		if type(result)==type(''):
			return unicode( result, 'utf-8' )
		elif type(result)==type([]):
			return map(self.convert, result)
		elif type(result)==type(()):
			return map(self.convert, result)
		elif type(result)==type({}):
			newres = {}
			for i in result.keys():
				newres[i] = self.convert(result[i])
			return newres
		else:
			return result

	def call(self, obj, method, *args):
		s = tiny_socket.mysocket()
		s.connect( self.url )
		# Remove leading slash (ie. '/object' -> 'object')
		obj = obj[1:]
		if self.authorized:
			s.mysend((obj, method, self.databaseName, self.uid, self.password)+args)
		else:
			s.mysend((obj, method)+args)
		res = s.myreceive()
		s.disconnect()
		return self.convert( res )

## @brief The XmlRpcConnection class implements Connection class for XML-RPC.
#
# The XML-RPC communication protocol is usually opened at port 8069 on the server.
class XmlRpcConnection(Connection):
	def call(self, obj, method, *args ):
		remote = xmlrpclib.ServerProxy(self.url + obj)
		function = getattr(remote, method)
		if self.authorized:
			result = function(self.databaseName, self.uid, self.password, *args)
		else:
			result = function( *args )
		return result

## Creates an instance of the appropiate Connection class (whether 
# SocketConnection or XmlRpcConnection) given an url. If the scheme (or
# protocol is socket:// opens SocketConnection. Otherwise (usually http)
# opens a XmlRpcConnection.
def createConnection(url):
	qUrl = QUrl( url )
	if qUrl.scheme() == 'socket':
		con = SocketConnection()
		con.url = url
		return con
	else:
		con = XmlRpcConnection()
		con.url = url + '/xmlrpc'
		return con

class AbstractCache:
	def exists( self, obj, method, *args ):
		pass
	def get( self, obj, method, *args ):
		pass

class ViewCache(AbstractCache):
	def __init__(self):
		self.cache = {}

	def exists(self, obj, method, *args):
		if method != 'execute' or len(args) < 2 or args[1] != 'fields_view_get':
			return False
		return (obj, method, str(args)) in self.cache
			
	def get(self, obj, method, *args):
		return copy.deepcopy( self.cache[(obj, method, str(args))] )
		
	def add(self, value, obj, method, *args):
		if method != 'execute' or len(args) < 2 or args[1] != 'fields_view_get':
			return
		self.cache[(obj,method,str(args))] = copy.deepcopy( value )

	def clear(self):
		self.cache = {}

## @brief The Session class provides a simple way of login and executing function in a server
#
# Typical usage of Session:
#
# \code
# import rpc
# rpc.session.login('http://admin:admin@localhost:8069', 'database')
# attached = rpc.session.execute('/object', 'execute', 'ir.attachment', 'read', [1,2,3])
# rpc.session.logout()
# \endcode
class Session:
	def __init__(self):
		self.open = False
		self.url = None
		self.password = None
		self.uid = None
		self.context = {}
		self.userName = None
		self.databaseName = None
		self.connection = None
		self.errorHandler = None
		self.cache = None

	## @brief Calls the specified method
	# on the given object on the server. 
	#
	# If there is an error during the call it simply rises an exception. See 
	# execute() if you want exceptions to be handled by the notify mechanism.
	# @param obj Object name (string) that contains the method
	# @param method Method name (string) to call 
	# @param args Argument list for the given method
	def call(self, obj, method, *args):
		if self.cache:
			if self.cache.exists( obj, method, *args ):
				return self.cache.get( obj, method, *args )
		value = self.connection.call(obj, method, *args)
		if self.cache:
			self.cache.add( value, obj, method, *args )
		return value

	## @brief Same as call() but uses the notify mechanism to notify
	# exceptions. 
	#
	# Note that you'll need to bind gettext as texts sent to
	# the notify module are localized.
	def execute(self, obj, method, *args):
		if not self.open:
			raise RpcException(1, 'not logged')
		try:
			#return self.connection.call(obj, method, *args)
			return self.call(obj, method, *args)
		except socket.error, err:
			notifier.notifyError(_('Connection Refused'), unicode(err), unicode(err) )
		except xmlrpclib.Fault, err:
			a = RpcException(err.faultCode, err.faultString)
			if a.type in ('warning','UserError'):
				notifier.notifyWarning(a.message, a.data )
			else:
				notifier.notifyError(_('Application Error'), _('View details'), err.faultString)

	## @brief Logs in the given server with specified name and password.
	# @param url url string such as 'http://admin:admin@localhost:8069'. 
	# Admited protocols are 'http', 'https' and 'socket'
	# @param db string with the database name 
	# Returns -1 if an exception occurred while trying to contact the server.
	# Returns -2 if the login information was refused by the server.
	def login(self, url, db):
		url = QUrl( url )
		_url = str( url.scheme() ) + '://' + str( url.host() ) + ':' + str( url.port() ) 
		self.connection = createConnection( _url )
		user = unicode( url.userName() )
		password = unicode( url.password() )
		try:
			res = self.connection.call( '/common', 'login', db, user, password )
		except socket.error, e:
			return -1
		if not res:
			self.open=False
			self.uid=False
			return -2

		self.url = _url
		self.open = True
		self.uid = res
		self.userName = user
		self.password = password
		self.databaseName = db
		if self.cache:
			self.cache.clear()
		
		self.connection.databaseName = self.databaseName
		self.connection.password = self.password
		self.connection.uid = self.uid
		self.connection.authorized = True

		self.reloadContext()
		return 1
	
	## @brief Reloads the session context
	#
	# Useful when some user parameters such as language are changed.
	def reloadContext(self):
		self.context = {}
		context = self.execute('/object', 'execute', 'ir.values', 'get', 'meta', False, [('res.users', self.uid or False)], False, {}, True, True, False)
		for c in context:
			if c[2]:
				self.context[c[1]] = c[2]

	## Returns whether the login function has been called and was successfull
	def logged(self):
		return self.open

	## Logs out of the server.
	def logout(self):
		if self.open:
			self.open = False
			self.userName = None
			self.uid = None
			self.password = None
			if self.cache:
				self.cache.clear()

	## Uses eval to evaluate the expression, using the defined context
	# plus the appropiate 'uid' in it.
	def evaluateExpression(self, expression, context={}):
		context['uid'] = self.uid
		if isinstance(expression, basestring):
			return eval(expression, context)
		else:
			return expression 

session = Session()
session.cache = ViewCache()

## The Database class handles queries that don't require a previous login, served by the db server object
class Database:
	## Obtains the list of available databases from the given URL. None if there 
	# was an error trying to fetch the list.
	def list(self, url):
		try:
			return self.call( url, 'list' )
		except:
			return -1

	## @brief Calls the specified method
	# on the given object on the server. If there is an error
	# during the call it simply rises an exception
	def call(self, url, method, *args):
		con = createConnection( url )
		return con.call( '/db', method, *args )

	## Same as call() but uses the notify mechanism to notify 
	#  exceptions.
	def execute(self, url, method, *args):
		res = False
		try:
			res = self.call(url, method, *args)
		except socket.error, msg:
			notifier.notifyWarning('', _('Could not contact server!') )
		return res

database = Database()

class RPCProxy(object):
	def __init__(self, resource):
		self.resource = resource
		self.__attrs = {}

	def __getattr__(self, name):
		if not name in self.__attrs:
			self.__attrs[name] = RPCFunction(self.resource, name)
		return self.__attrs[name]
	

class RPCFunction(object):
	def __init__(self, object, func_name):
		self.object = object
		self.func = func_name

	def __call__(self, *args):
		return session.execute('/object', 'execute', self.object, self.func, *args)

