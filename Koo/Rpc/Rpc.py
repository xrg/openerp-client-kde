##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007-2010 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (c) 2010 P. Christeas <p_christ@hol.gr>
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
from Koo.Common import Notifier
from Koo.Common import Url
import xmlrpclib
import socket
import tiny_socket
import logging
from Cache import *
from Koo.Common.safe_eval import safe_eval

ConcurrencyCheckField = '__last_update'

class RpcException(Exception):
	def __init__(self, info):
		self.code = None
		self.args = (info,)
		self.info = info
		self.backtrace = None

class RpcProtocolException(RpcException):
	def __init__(self, backtrace):
		self.code = None
		self.args = (backtrace,)
		self.info = unicode( str(backtrace), 'utf-8' )
		self.backtrace = backtrace

class RpcServerException(RpcException):
	def __init__(self, code, backtrace):
		self.code = code
		if hasattr(code, 'split'):
			lines = code.split('\n')

			self.type = lines[0].split(' -- ')[0]
			msg = ''
			if len(lines[0].split(' -- ')) > 1:
				msg = lines[0].split(' -- ')[1]
			else:
				msg = lines[0]
			
			if len(lines) > 1:
				data = '\n'.join(lines[2:])
			else:
				data = backtrace
	
			self.args = ( msg, data )
		else:
			self.type = 'error'
			self.args = (backtrace, backtrace)

		self.backtrace = backtrace
	def __str__(self):
		if self.backtrace and '\n' in self.backtrace:
			bt = self.backtrace.split("\n")[-3:-2]
			bt = " ".join(bt)
		else:
			bt = self.backtrace
		return "<RpcServerException %s: '%s', '%s' >" % \
			(self.type, self.code, bt)

## @brief The Connection class provides an abstract interface for a RPC
# protocol
class Connection:
	def __init__(self, url):
		self.authorized = False
		self.databaseName = None
		self.uid = None
		self.password = None
		self.url = url
		self._log = logging.getLogger('RPC.Connection')

	def copy(self):
		newob = self.__class__(self.url)
		newob.authorized = self.authorized
		newob.databaseName = self.databaseName
		newob.uid = self.uid
		newob.password = self.password
		return newob
		
	def stringToUnicode(self, result): 
		if isinstance(result, str):
			return unicode( result, 'utf-8' )
		elif isinstance(result, list):
			return [self.stringToUnicode(x) for x in result]
		elif isinstance(result, tuple):
			return tuple([self.stringToUnicode(x) for x in result])
		elif isinstance(result, dict):
			newres = {}
			for i in result.keys():
				newres[i] = self.stringToUnicode(result[i])
			return newres
		else:
			return result

	def unicodeToString(self, result): 
		if isinstance(result, unicode):
			return result.encode( 'utf-8' )
		elif isinstance(result, list):
			return [self.unicodeToString(x) for x in result]
		elif isinstance(result, tuple):
			return tuple([self.unicodeToString(x) for x in result])
		elif isinstance(result, dict):
			newres = {}
			for i in result.keys():
				newres[i] = self.unicodeToString(result[i])
			return newres
		else:
			return result

	def connect(self, database, uid, password):
		self.databaseName = database
		self.uid = uid
		self.password = password

	def call(self, path, method, args=None, auth_level='db' ):
		raise NotImplementedError()
		
	def login(self, database, user, password):
		saved_creds = (self.databaseName, self.uid, self.password)
		try:
			self.databaseName = database
			self.uid = None
			self.password = password
			res = self.call( '/common', 'login', (database, user, password) )
			if not res:
				self.databaseName, self.uid, self.password = saved_creds
			else:
				assert isinstance(res, int)
				self.authorized = True
				self.uid = res
			return res
		except:
			self.databaseName, self.uid, self.password = saved_creds
			raise

modules = []
try:
	import Pyro.core
	modules.append( 'pyro' )
except:
	pass

## @brief The PyroConnection class implements Connection for the Pyro RPC protocol.
#
# The Pyro protocol is usually opened at port 8071 on the server.
class PyroConnection(Connection):
	def __init__(self, url):
		Connection.__init__(self, url)
		self.url += '/rpc'
		self.proxy = Pyro.core.getProxyForURI( self.url )

	def singleCall(self, obj, method, *args):
		encodedArgs = self.unicodeToString( args )
		if self.authorized:
			result = self.proxy.dispatch( obj[1:], method, self.databaseName, self.uid, self.password, *encodedArgs )
		else:
			result = self.proxy.dispatch( obj[1:], method, *encodedArgs )
		return self.stringToUnicode( result )

	def call(self, obj, method, args= None, auth_level='db'):
		try:
			try:
				#import traceback
				#traceback.print_stack()
				#print "CALLING: ", obj, method, args
				result = self.singleCall( obj, method, *args )
			except (Pyro.errors.ConnectionClosedError, Pyro.errors.ProtocolError), x:
				# As Pyro is a statefull protocol, network errors
				# or server reestarts will cause errors even if the server
				# is running and available again. So if remote call failed 
				# due to network error or server restart, try to bind 
				# and make the call again.
				self.proxy = Pyro.core.getProxyForURI( self.url )
				result = self.singleCall( obj, method, *args )
		except (Pyro.errors.ConnectionClosedError, Pyro.errors.ProtocolError), err:
			raise RpcProtocolException( unicode( err ) )
		except Exception, err:
			if Pyro.util.getPyroTraceback(err):
				faultCode = err.message
				faultString = u''
				for x in Pyro.util.getPyroTraceback(err):
					faultString += unicode( x, 'utf-8', errors='ignore' )
				raise RpcServerException( faultCode, faultString )
			raise
		return result

## @brief The SocketConnection class implements Connection for the OpenERP socket RPC protocol.
#
# The socket RPC protocol is usually opened at port 8070 on the server.
class SocketConnection(Connection):
	def call(self, obj, method, args, auth_level='db'):
		try:
			s = tiny_socket.mysocket()
			s.connect( self.url )
		except socket.error, err:
			raise RpcProtocolException( unicode(err) )
		try:
			# Remove leading slash (ie. '/object' -> 'object')
			obj = obj[1:]
			encodedArgs = self.unicodeToString( args )
			if self.authorized:
				s.mysend( (obj, method, self.databaseName, self.uid, self.password) + encodedArgs )
			else:
				s.mysend( (obj, method) + encodedArgs )
			result = s.myreceive()
		except socket.error, err:
			# print err.strerror
			raise RpcProtocolException( err.strerror )
		except tiny_socket.Myexception, err:
			faultCode = unicode( err.faultCode, 'utf-8' )
			faultString = unicode( err.faultString, 'utf-8' )
			raise RpcServerException( faultCode, faultString )
		finally:
			s.disconnect()
		return self.stringToUnicode( result )

session_counter = 0
## @brief The XmlRpcConnection class implements Connection class for XML-RPC.
#
# The XML-RPC communication protocol is usually opened at port 8069 on the server.
class XmlRpcConnection(Connection):
	def __init__(self, url):
		Connection.__init__(self, url)
		self.url += '/xmlrpc'
		self._ogws = {}

	def copy(self):
		newob = Connection.copy(self)
		newob.url = self.url

	def gw(self,obj):
		""" Return the persistent gateway for some object
		"""
		global session_counter
		if not self._ogws.has_key(obj):
			if self.url.startswith("https"):
				transport = tiny_socket.SafePersistentTransport()
			elif self.url.startswith("http"):
				transport = tiny_socket.PersistentTransport()
			else:
				transport = None
			self._ogws[obj] = xmlrpclib.ServerProxy(self.url + obj, transport=transport)
			
			session_counter = session_counter + 1
			if (session_counter % 100) == 0:
				self._log.debug("Sessions: %d", session_counter)
		
		return self._ogws[obj]

	def call(self, obj, method, args, auth_level='db'):
		remote = self.gw(obj)
		function = getattr(remote, method)
		try:
			if self.authorized:
				result = function(self.databaseName, self.uid, self.password, *args)
			else:
				result = function( *args )
		except socket.error, err:
			print "socket.error",err
			raise RpcProtocolException( err )
		except xmlrpclib.Fault, err:
			raise RpcServerException( err.faultCode, err.faultString )
		except Exception, e:
			print "Exception:",e
			raise
		return result


## @brief Connection class for the xml-rpc 2.0 OpenObject protocol
#
# This protocol is implemented at the same port as the xmlrpc 1.0, but has a
# different authentication mechanism.
#
class XmlRpc2Connection(Connection):
	def __init__(self, url):
		Connection.__init__(self, url)
		self.url += '/xmlrpc2'
		self._ogws = {}
		self.username = None
		self._authclient = None
		
	def copy(self):
		newob = Connection.copy(self)
		newob.username = self.username
		newob.url = self.url
		newob._authclient = self._authclient
		# Note: we don't copy the _ogws, so that new connections
		# are launched (not reuse the persistent ones)
		
		return newob
		
	def gw(self, obj, auth_level, temp=False):
		""" Return the persistent gateway for some object
		
		    If temp is specified, the proxy is a temporary one,
		    not from cache. This is needed at the login, where the
		    proxy could fail and need to be discarded.
		"""
		global session_counter
		if temp or not self._ogws.has_key(obj):
			if self.url.startswith("https"):
				transport = tiny_socket.SafePersistentAuthTransport()
			elif self.url.startswith("http"):
				transport = tiny_socket.PersistentAuthTransport()
			else:
				transport = None
			
			path = self.url
			if not path.endswith('/'):
				path += '/'
			path += auth_level
			if auth_level == 'db':
				path += '/' + self.databaseName
			path += obj
			# self._log.debug("path: %s %s", path, obj)
			
			if temp and transport:
				transport.setAuthTries(1)
				
			if self._authclient and transport:
				transport.setAuthClient(self._authclient)
			
			nproxy = xmlrpclib.ServerProxy( path, transport=transport)
			
			session_counter = session_counter + 1
			if (session_counter % 100) == 0:
				self._log.debug("Sessions: %d", session_counter)
				
			if temp:
				if transport:
					transport.setAuthTries(3)
				return nproxy
			
			self._ogws[obj] = nproxy
		
		return self._ogws[obj]

	def call(self, obj, method, args, auth_level='db'):
		remote = self.gw(obj, auth_level)
		function = getattr(remote, method)
		try:
			result = function( *args )
		except socket.error, err:
			self._log.error("socket error: %s" % err)
			raise RpcProtocolException( err )
		except xmlrpclib.Fault, err:
			self._log.error( "xmlrpclib.Fault on %s/%s(%s): %s" % (obj,str(method), args[:2], err.faultCode))
			raise RpcServerException( err.faultCode, err.faultString )
		except Exception, e:
			self._log.exception("Exception:")
			raise
		return result

	def call2(self, obj, method, args, auth_level='db'):
		""" Variant of call(), with a temporary gateway, for login """
		remote = self.gw(obj, auth_level, temp=True)
		function = getattr(remote, method)
		try:
			result = function( *args )
			if result:
				# do cache the proxy, now that it's successful
				self._ogws[obj] = remote
		except socket.error, err:
			self._log.error("socket error: %s" % err)
			raise RpcProtocolException( err )
		except xmlrpclib.Fault, err:
			self._log.error( "xmlrpclib.Fault on %s/%s(%s): %s" % (obj,str(method), str(args[:2]), err))
			raise RpcServerException( err.faultCode, err.faultString )
		except Exception, e:
			self._log.exception("Exception:")
			raise
		return result

	def login(self, database, user, password):
		saved_creds = (self.databaseName, self.username, self.uid, self.password, self._authclient)
		try:
			self.databaseName = database
			self.username = user
			self.uid = None
			self.password = password
			self._authclient = tiny_socket.BasicAuthClient()
			self._authclient.addLogin("OpenERP User", user, password)
			res = self.call2( '/common', 'login', (database, user, password) )
			if not res:
				self.databaseName, self.username, self.uid, self.password, self._authclient = saved_creds
			return res
		except:
			self.databaseName, self.username, self.uid, self.password, self._authclient = saved_creds
			raise

## @brief Creates an instance of the appropiate Connection class.
#
# These can be:
# - SocketConnection if protocol (or scheme) is socket:// 
# - PyroConnection if protocol 
# - XmlRpcConnection otherwise (usually will be http or https)
def createConnection(url):
	qUrl = QUrl( url )
	if qUrl.scheme() == 'socket':
		con = SocketConnection( url )
	elif qUrl.scheme() == 'PYROLOC':
		con = PyroConnection( url )
	else:
		con = XmlRpc2Connection( url )
	return con

class AsynchronousSessionCall(QThread):
	def __init__(self, session, parent=None):
		QThread.__init__(self, parent)
		self.session = session.copy()
		self.obj = None
		self.method = None
		self.args = None
		self.result = None
		self.callback = None
		self.error = None
		self.warning = None
		self.exception = None
		# If false, the behaviour is the same as Session.call()
		# otherwise we use the notification mechanism and behave
		# like Session.execute()
		self.useNotifications = False

	def execute(self, callback, obj, method, *args):
		self.useNotifications = True
		self.exception = None
		self.callback = callback
		self.obj = obj
		self.method = method
		self.args = args
		self.connect( self, SIGNAL('finished()'), self.hasFinished )
		self.start()

	def call(self, callback, obj, method, *args):
		self.useNotifications = False
		self.exception = None
		self.callback = callback
		self.obj = obj
		self.method = method
		self.args = args
		self.connect( self, SIGNAL('finished()'), self.hasFinished )
		self.start()

	def hasFinished(self):
		if self.exception:
			if self.useNotifications:
				# Note that if there's an error or warning
				# callback is called anyway with value None
				if self.error:
					Notifier.notifyError(*self.error)
				elif self.warning:
					Notifier.notifyWarning(*self.warning)
				else:
					raise self.exception
			self.emit( SIGNAL('exception(PyQt_PyObject)'), self.exception )
		else:
			self.emit( SIGNAL('called(PyQt_PyObject)'), self.result )

		if self.callback:
			self.callback( self.result, self.exception )

		# Free session and thus server connections as soon as possible
		self.session = None

	def run(self):
		# As we don't want to force initialization of gettext if 'call' is used
		# we handle exceptions depending on 'useNotifications' 
		if not self.useNotifications:
			try:
				self.result = self.session.call( self.obj, self.method, *self.args )
			except Exception, err:
				self.exception = err
		else:
			try:
				self.result = self.session.call( self.obj, self.method, *self.args )
			except RpcProtocolException, err:
				self.exception = err
				self.error = (_('Connection Refused'), err.info, err.info)
			except RpcServerException, err:
				self.exception = err
				if err.type in ('warning','UserError'):
					self.warning = tuple(err.args[0:2])
				else:
					self.error = (_('Application Error'), _('View details'), err.backtrace )


## @brief The Session class provides a simple way of login and executing function in a server
#
# Typical usage of Session:
#
# \code
# from Koo import Rpc
# Rpc.session.login('http://admin:admin\@localhost:8069', 'database')
# attached = Rpc.session.execute('/object', 'execute', 'ir.attachment', 'read', [1,2,3])
# Rpc.session.logout()
# \endcode
class Session:
	LoggedIn = 1
	Exception = 2
	InvalidCredentials = 3
	
	def __init__(self):
		self.open = False
		self.url = None
		#self.password = None
		self.uid = None
		self.context = {}
		self.userName = None
		self.databaseName = None
		self.connection = None
		self.cache = None
		self.threads = []
		self._log = logging.getLogger('RPC.Session')

	# This function removes all finished threads from the list of running
	# threads and appends the one provided.
	# We keep a reference to all threads started because otherwise their
	# C++ counterparts would be freed by garbage collector. User can also
	# keep a reference to it when she calls callAsync or executeAsync but
	# with this mechanism she's not forced to it.
	# The only inconvenience we could find is that we kept some thread
	# objects for much too long in memory, but that doesn't seem worrisome
	# by now.
	def appendThread(self, thread):
		self.threads = [x for x in self.threads if x.isRunning()]
		self.threads.append( thread )

	## @brief Calls asynchronously the specified method on the given object on the server.
	# 
	# When the response to the request arrives the callback function is called with the
	# returned value as the first parameter. It returns an AsynchronousSessionCall instance 
	# that can be used to keep track to what query a callback refers to, consider that as
	# a call id.
	# If there is an error during the call it simply rises an exception. See 
	# execute() if you want exceptions to be handled by the notification mechanism.
	# @param callback Function that has to be called when the result returns from the server.
	# @param exceptionCallback Function that has to be called when an exception returns from the server.
	# @param obj Object name (string) that contains the method
	# @param method Method name (string) to call 
	# @param args Argument list for the given method
	# 
	# Example of usage:
	# \code
	# from Koo import Rpc
	# def returned(self, value):
	# 	print value
	# Rpc.session.login('http://admin:admin\@localhost:8069', 'database')
	# Rpc.session.post( returned, '/object', 'execute', 'ir.attachment', 'read', [1,2,3]) 
	# Rpc.session.logout()
	# \endcode
	def callAsync( self, callback, exceptionCallback, obj, method, *args ):
		caller = AsynchronousSessionCall( self )
		caller.call( callback, obj, method, *args )
		self.appendThread( caller )
		return caller

	## @brief Same as callAsync() but uses the notify mechanism to notify
	# exceptions. 
	#
	# Note that you'll need to bind gettext as texts sent to
	# the notify module are localized.
	def executeAsync( self, callback, obj, method, *args ):
		caller = AsynchronousSessionCall( self )
		caller.execute( callback, obj, method, *args )
		#print "exec async args:", args
		self.appendThread( caller )
		return caller

	## @brief Calls the specified method
	# on the given object on the server. 
	#
	# If there is an error during the call it simply rises an exception. See 
	# execute() if you want exceptions to be handled by the notification mechanism.
	# @param obj Object name (string) that contains the method
	# @param method Method name (string) to call 
	# @param args Argument list for the given method
	def call(self, obj, method, *args):
		if not self.open:
			raise RpcException(_('Not logged in'))
		if self.cache:
			if self.cache.exists( obj, method, *args ):
				return self.cache.get( obj, method, *args )
		value = self.connection.call(obj, method, args)
		if self.cache:
			self.cache.add( value, obj, method, *args )
		return value

	## @brief Same as call() but uses the notify mechanism to notify
	# exceptions. 
	#
	# Note that you'll need to bind gettext as texts sent to
	# the notify module are localized.
	def execute(self, obj, method, *args):
		try:
			return self.call(obj, method, *args)
		except RpcProtocolException, err:
			Notifier.notifyError(_('Connection Refused'), err.info, err.info )
			raise
		except RpcServerException, err:
			if err.type in ('warning','UserError'):
				if err.args[0] in ('ConcurrencyException') and len(args) > 4:
					if Notifier.notifyConcurrencyError(args[0], args[2] and args[2][0], args[4]):
						if ConcurrencyCheckField in args[4]:
							del args[4][ConcurrencyCheckField]
						return self.execute(obj, method, *args)
				else:
					Notifier.notifyWarning(err.args[0], err.args[1])
			else:
				Notifier.notifyError(_('Application Error'), _('View details'), err.backtrace )
			raise
		except Exception,e:
			self._log.exception("Execute:")
			pass


	## @brief Logs in the given server with specified name and password.
	# @param url url string such as 'http://admin:admin\@localhost:8069'. 
	# Admited protocols are 'http', 'https' and 'socket'
	# @param db string with the database name 
	# Returns Session.Exception, Session.InvalidCredentials or Session.LoggedIn
	def login(self, url, db):
		url = QUrl( url )
		_url = str( url.scheme() ) + '://' + str( url.host() ) + ':' + str( url.port() ) 
		self.connection = createConnection( _url )
		user = Url.decodeFromUrl( unicode( url.userName() ) )
		password = Url.decodeFromUrl( unicode( url.password() ) )
		try:
			res = self.connection.login(db, user, password)
			self._log.info('Logged into %s as %s', db, user)
		except socket.error, e:
			return Session.Exception
		except tiny_socket.ProtocolError, e:
			self._log.error('Protocol error: %s', e)
			return Session.InvalidCredentials
		except Exception, e:
			self._log.exception("login call exception:")
			return Session.Exception
		if not res:
			self.open=False
			self.uid=False
			return Session.InvalidCredentials

		self.url = _url
		self.open = True
		self.uid = res
		self.userName = user
		#self.password = password
		self.databaseName = db
		if self.cache:
			self.cache.clear()
		
		self.reloadContext()
		return Session.LoggedIn

	## @brief Reloads the session context
	#
	# Useful when some user parameters such as language are changed.
	def reloadContext(self):
		self.context = self.execute('/object', 'execute', 'res.users', 'context_get') or {}

	## @brief Returns whether the login function has been called and was successfull
	def logged(self):
		return self.open

	## @brief Logs out of the server.
	def logout(self):
		if self.open:
			self.open = False
			#self.userName = None
			self.uid = None
			#self.password = None
			self.connection = None
			if self.cache:
				self.cache.clear()

	## @brief Uses eval to evaluate the expression, using the defined context
	# plus the appropiate 'uid' in it.
	def evaluateExpression(self, expression, context=None):
		if context is None:
			context = {}
		#else:
		#	ctx = context.copy()
		context['uid'] = self.uid
		if isinstance(expression, basestring):
			try:
			        expression = expression.replace("'active_id'","active_id")
				return safe_eval(expression, context)
			except Exception, e:
				self._log.exception( "Exception: %s for \"%s\" " %( e, expression))
				raise
		else:
			return expression

	def copy(self):
		new = Session()
		new.open = self.open 
		new.url = self.url 
		# new.password = self.password
		new.uid = self.uid
		new.context = self.context
		new.userName = self.userName
		new.databaseName = self.databaseName
		new.connection = self.connection.copy()
		return new

session = Session()
session.cache = ActionViewCache()

## @brief The Database class handles queries that don't require a previous login, served by the db server object
class Database:
	## @brief Obtains the list of available databases from the given URL. None if there 
	# was an error trying to fetch the list.
	def list(self, url):
		try:
			return self.call( url, 'list' )
		except Exception,e:
			logging.getLogger('RPC.Database').exception("db list exc:")
			return -1

	## @brief Calls the specified method
	# on the given object on the server. If there is an error
	# during the call it simply rises an exception
	def call(self, url, method, *args):
		con = createConnection( url )
		if method in [ 'db_exist', 'list', 'list_lang', 'server_version']:
		    authl = 'pub'
		else:
		    authl = 'root'
		return con.call( '/db', method, args, auth_level=authl)

	## @brief Same as call() but uses the notify mechanism to notify 
	# exceptions.
	def execute(self, url, method, *args):
		res = False
		try:
			res = self.call(url, method, *args)
		except socket.error, msg:
			Notifier.notifyWarning('', _('Could not contact server!') )
		return res

database = Database()

## @brief The RpcProxy class allows wrapping a server object only by giving it's name.
# 
# For example: 
# obj = RpcProxy('ir.values')
class RpcProxy(object):
	def __init__(self, resource):
		self.resource = resource
		self.__attrs = {}

	def __getattr__(self, name):
		if not name in self.__attrs:
			self.__attrs[name] = RpcFunction(self.resource, name)
		return self.__attrs[name]
	

class RpcFunction(object):
	def __init__(self, object, func_name):
		self.object = object
		self.func = func_name

	def __call__(self, *args):
		return session.execute('/object', 'execute', self.object, self.func, *args)

