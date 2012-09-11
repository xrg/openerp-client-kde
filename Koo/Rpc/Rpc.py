##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007-2010 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (c) 2010-2011 P. Christeas <xrg@linux.gr>
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

from PyQt4.QtCore import QThread, SIGNAL, QUrl, QVariant, QTimer

try:
	from PyQt4.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
	isQtNetworkAvailable = True
except ImportError:
	isQtNetworkAvailable = False

from Koo.Common import Notifier
from Koo.Common import Url
from Koo.Common import Api 
from Koo.Common import Debug # TODO

import logging
import base64 # FIXME
import traceback
import time
from Koo.Common.safe_eval import safe_eval

from openerp_libclient.rpc import RpcFunction, RpcProxy, RpcCustomProxy
from openerp_libclient.session import Session
from openerp_libclient import rpc as client_rpc
from openerp_libclient.interface import RPCNotifier
from openerp_libclient.errors import RpcException, RpcNetworkException, RpcProtocolException, RpcServerException

ConcurrencyCheckField = '__last_update'



class AsynchronousSessionCall(QThread):
	def __init__(self, session, parent=None):
		QThread.__init__(self, parent)
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
                                # Decode the exception stored by run()
                                
                                err = self.exception
                                if isinstance(err, RpcProtocolException):
                                    Notifier.notifyError(_('Connection Refused'), err.info, err.info)
                                elif isinstance(err, RpcServerException):
                                    if err.type in ('warning','UserError'):
                                            self.warning = tuple(err.args[0:2])
                                            Notifier.notifyWarning(*self.warning)
                                    else:
                                            Notifier.notifyError(_('Application Error: %s') % err.get_title(),
                                                    _('View details: %s') % err.get_details(),
                                                    err.backtrace )
                                else:
                                        raise self.exception

                        # Note that if there's an error or warning
                        # callback is called anyway with value None
			self.emit( SIGNAL('exception(PyQt_PyObject)'), self.exception )
		else:
			self.emit( SIGNAL('called(PyQt_PyObject)'), self.result )

		if self.callback:
			self.callback( self.result, self.exception )

	def run(self):
            global session
            # As we don't want to force initialization of gettext if 'call' is used
            # we handle exceptions depending on 'useNotifications' 
            try:
                    self.result = session.call( self.obj, self.method, self.args, 
                                notify=False)
                                # we want no GUI notifications in this thread!
            except Exception, err:
                    self.exception = err

class _proxy_session(object):
    """ Will behave like openerp_libclient.session.Session, but
        will be immutable, safe to import only once
    """
    def __init__(self):
        self.__threads = []

    def execute(self, obj, method, *args):
        return client_rpc.default_session.call(obj, method, args)

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
            self.__threads = [x for x in self.__threads if x.isRunning()]
            self.__threads.append( thread )

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
    #       print value
    # Rpc.session.login('http://admin:admin\@localhost:8069', 'database')
    # Rpc.session.post( returned, '/object', 'execute', 'ir.attachment', 'read', [1,2,3]) 
    # Rpc.session.logout()
    # \endcode
    def callAsync( self, callback, obj, method, *args ):
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

    ## @brief Uses eval to evaluate the expression, using the defined context
    # plus the appropiate 'uid' in it.
    def evaluateExpression(self, expression, context=None):
        if context is None:
                context = {}
        #else:
        #       ctx = context.copy()
        cglobals = dict(uid=self.get_uid(), time=time)
        if isinstance(expression, basestring):
            try:
                expression = expression.replace("'active_id'","active_id")
                return safe_eval(expression, cglobals, context)
            except Exception, e:
                self._log.error( "Exception: %s for \"%s\" " %( e, expression))
                import traceback
                self._log.warning('Caller Trace:\n' + ''.join(traceback.format_stack(limit=5)[:-1]))
                raise
        else:
            return expression

    def __getattr__(self, name):
        return getattr(client_rpc.default_session, name)

    def __nonzero__(self):
        return client_rpc.default_session is not None

session = _proxy_session()
# session.cache = ActionViewCache()

def _url2conndict(url):
    """Analyze a string URL to the connection dictionary (for libclient)
    """
    qurl = QUrl( url )
    
    ret = dict(proto=str(qurl.scheme()), host=str(qurl.host()), port=str(qurl.port()),
            user=Url.decodeFromUrl(unicode(qurl.userName())),
            passwd=Url.decodeFromUrl(unicode(qurl.password())))
    if qurl.path():
        print "path", qurl.path()
        ret['dbname']=str(qurl.path().split('/',1)[0])
    return ret
    
## @brief The Database class handles queries that don't require a previous login, served by the db server object
class Database:
	## @brief Obtains the list of available databases from the given URL. None if there 
	# was an error trying to fetch the list.
	def list(self, url):
		try:
			call = self.call( url, 'list' )
		except RpcServerException, e:
			if e.type == 'AccessDenied':
				# The server has been configured to not return
				# the list of available databases.
				call = False
			else:
				call = -1
		except Exception,e:
			logging.getLogger('RPC.Database').exception("db list exc:")
			call = -1
		finally:
			return call

	## @brief Calls the specified method
	# on the given object on the server. If there is an error
	# during the call it simply rises an exception
	def call(self, url, method, *args):
                sess = Session()
                urldict = _url2conndict(url)
                sess.open(**urldict)
		if method in [ 'db_exist', 'list', 'list_lang', 'server_version']:
		    authl = 'pub'
		else:
		    authl = 'root'
		return sess.call( '/db', method, args, auth_level=authl, notify=False)

	## @brief Same as call() but uses the notify mechanism to notify 
	# exceptions.
	def execute(self, url, method, *args):
		res = False
		try:
			res = self.call(url, method, *args, notify=True)
		except RpcProtocolException, msg:
			# Notifier.notifyWarning('', _('Could not contact server!') )
			pass
		return res

database = Database()


class KooNotifier(RPCNotifier):
    """ Notifications using the GUI
    """

    def __init__(self):
        RPCNotifier.__init__(self)

    def handleException(self, msg, *args, **kwargs):
        """
            @param exc must be a tuple of exception information, from sys.exc_info(), or None
        """
        exc_info = None
        title = _("Koo Error!")
        do_traceback = True
        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            if exc_info[0] == RpcNetworkException:
                title = _("Network Error!")
                do_traceback = False
        if do_traceback:
            details = traceback.format_exc(8)
        else:
            details = ''
        Notifier.notifyError(title, msg % args, details)
        super(KooNotifier, self).handleException(msg, *args, **kwargs)

    def handleRemoteException(self, msg, *args, **kwargs):
        """
            @param exc must be a tuple of exception information, from sys.exc_info(), or None
        """
        exc_info = kwargs.get('exc_info', False)
        title = _("Exception at Server!")
        message = msg % args
        details = ''
        if kwargs.get('frame_info'):
            details += "Local Traceback (most recent call last):\n" \
                    + ''.join(traceback.format_stack(kwargs['frame_info'], 8))
        if exc_info:
            details += "\nRemote %s" % exc_info[1].backtrace
        if isinstance(exc_info[1], RpcServerException):
            title = exc_info[1].get_title()
            message = exc_info[1].get_details()
            if exc_info[1].type == 'warning':
                Notifier.notifyWarning(title, message)
                return
            else:
                message += '\n' + message

        Notifier.notifyError(title, message, details)
        super(KooNotifier, self).handleRemoteException(msg, *args, **kwargs)

    def handleError(self, msg, *args):
        Notifier.notifyWarning(_("Error!"), msg % args)
        super(KooNotifier, self).handleError(msg, *args)

    def handleWarning(self, msg, *args, **kwargs):
        """ Issue a warning to user.
            TODO: auto_close
        """
        Notifier.notifyWarning(_("Warning"), msg % args)
        super(KooNotifier, self).warning(msg, *args, **kwargs)

    def userAlert(self, msg, *args):
        """Tell the user that something happened and continue
        """
        Notifier.notifyWarning(_("Notice"), msg % args)
        super(KooNotifier, self).userAlert(msg, *args)

def login_session(url, dbname):
    """ Initialize the global session and open it to url/dbname
    """
    if client_rpc.default_session:
        client_rpc.default_session.logout()

    udict = _url2conndict(url)
    if dbname:
        udict['dbname'] = dbname
    udict['notifier'] = KooNotifier()
    udict['conn_expire'] = True
    client_rpc.openSession(**udict)
    l = client_rpc.login()
    if not l:
        return False

    return l

if isQtNetworkAvailable:
	# @brief RpcReply class extends QNetworkReply and adds a new 'openerp://' protocol to access content through the current Rpc.session connection.
	#
	# URL should be of the form openerp://res.model/function/path_sent_to_the_function
	class RpcReply(QNetworkReply):
		def __init__(self, parent, url, operation):
			QNetworkReply.__init__(self, parent)

			path = unicode( url.path() )
			path = path.split('/')
			if unicode( url.host() ) == 'client':
				function = path[-1]
				parameters = [[unicode(x[0]), unicode(x[1])] for x in url.queryItems()]
				parameters = dict(parameters)
				if 'res_id' in parameters:
					try:
						parameters['res_id'] = int(parameters['res_id'])
					except ValueError:
						parameters['res_id'] = False

				if function == 'action':
					Api.instance.executeAction(parameters, data={}, context=session.context)
					
				return
			elif len(path) >= 3:
				model = unicode( url.host() )
				function = path[1]
				parameter = '/%s' % '/'.join( path[2:] )

				try:
					self.content = session.call('/object','execute', model, function, parameter, session.context)
				except:
					self.content = ''
				if self.content:
					self.content = base64.decodestring( self.content )
				else:
					self.content = ''
			else:
				self.content = ''

			self.offset = 0

			self.setHeader(QNetworkRequest.ContentTypeHeader, QVariant("text/html; charset=utf-8"))
			self.setHeader(QNetworkRequest.ContentLengthHeader, QVariant(len(self.content)))
			QTimer.singleShot(0, self, SIGNAL("readyRead()"))
			QTimer.singleShot(0, self, SIGNAL("finished()"))
			self.open(self.ReadOnly | self.Unbuffered)
			self.setUrl(url)

		def abort(self):
			pass

		def bytesAvailable(self):
			return len(self.content) - self.offset

		def isSequential(self):
			return True

		def readData(self, maxSize):
			if self.offset < len(self.content):
				end = min(self.offset + maxSize, len(self.content))
				data = self.content[self.offset:end]
				self.offset = end
				return data

	# @brief RpcNetworkAccessManager class extends QNetworkAccessManager and adds a new 'openerp://' protocol to access content through the current Rpc.session connection.
	class RpcNetworkAccessManager( QNetworkAccessManager ):
		def __init__(self, oldManager):
			QNetworkAccessManager.__init__(self)
			self.oldManager = oldManager
			self.setCache(oldManager.cache())
			self.setCookieJar(oldManager.cookieJar())
			self.setProxy(oldManager.proxy())
			self.setProxyFactory(oldManager.proxyFactory())

		def createRequest(self, operation, request, data):
			if request.url().scheme() != 'openerp':
				return QNetworkAccessManager.createRequest(self, operation, request, data)

			if operation != self.GetOperation:
				return QNetworkAccessManager.createRequest(self, operation, request, data)

			return RpcReply(self, request.url(), self.GetOperation)

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
