##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
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

from threading import Thread
import Pyro.core
import netsvc
import tools
import release

logger = netsvc.Logger()

class PyroDaemon(Thread):
	def __init__(self, host, port, ssl=False, settings=False):
		Thread.__init__(self)
		self.__host = host
		self.__port = port
		self.__ssl = ssl
		self.__settings = settings

	def run(self):
		class RpcDispatcher(Pyro.core.ObjBase, netsvc.OpenERPDispatcher):
			def dispatch(self, obj, methodName, *args):
				try:
					return netsvc.OpenERPDispatcher.dispatch(self, obj, methodName, args)
				except netsvc.OpenERPDispatcherException, e:
            				raise Pyro.core.PyroError(tools.exception_to_unicode(e.exception), e.traceback)

		Pyro.core.initServer(storageCheck=0)
		try:
			if self.__settings is not False:
				for k,v in self.__settings.items():
					setattr(Pyro.config,k,v)
			logger.notifyChannel("web-services", netsvc.LOG_INFO, "starting Pyro %s services, host %s, port %s" % (Pyro.core.Pyro.constants.VERSION, self.__host, self.__port))
			if self.__ssl is True:
				daemon=Pyro.core.Daemon(host=self.__host, port=self.__port, prtcol='PYROSSL')
			else:
				daemon=Pyro.core.Daemon(host=self.__host, port=self.__port)
			uri=daemon.connectPersistent( RpcDispatcher(), "rpc" )
			daemon.requestLoop()
		except Exception, e:
			import traceback
			logger.notifyChannel("web-services", netsvc.LOG_ERROR, "Pyro exception: %s\n%s" % (e, traceback.format_exc()))
			raise


tools.config['pyrohost'] = tools.config.get('pyrohost', None)
tools.config['pyrossl'] = tools.config.get('pyrossl', True)
tools.config['pyrossl_port'] = tools.config.get('pyrossl_port', 8072)
try:
	if tools.config['pyrossl']:
		version = Pyro.core.Pyro.constants.VERSION.split('.')
		if int(version[0]) <= 3 and int(version[1]) <= 10:
			logger.notifyChannel("init", netsvc.LOG_ERROR, "Need at least Pyro version 3.10 for SSL, found %s" % Pyro.core.Pyro.constants.VERSION)
		else:
			try:
				import M2Crypto
			except Exception, e:
				tools.config['pyrossl'] =  False
				logger.notifyChannel("init", netsvc.LOG_ERROR, "M2Crypto could not be imported, SSL will not work: %s" % (e.args) )
			else:
				try:
					pyrossl_port = int(tools.config["pyrossl_port"])
				except Exception:
					logger.notifyChannel("init", netsvc.LOG_ERROR, "invalid ssl port '%s'!" % (tools.config["pyroport-ssl"]) )
				settings = {}
				settings['PYROSSL_CERTDIR'] = tools.config.get('pyrossl_certdir', False)
				if settings['PYROSSL_CERTDIR'] is False:
					logger.notifyChannel("init", netsvc.LOG_ERROR, "pyrossl_certdir must be set!" )
				else:
					settings['PYROSSL_POSTCONNCHECK'] = tools.config.get('pyrossl_postconncheck',1)
					settings['PYROSSL_CERT'] = tools.config.get('pyrossl_cert','server.pem')
					settings['PYROSSL_CA_CERT'] = tools.config.get('pyrossl_ca_cert','ca.pem')
					settings['PYROSSL_KEY'] = tools.config.get('pyrossl_key',None)
					settings['PYRO_TRACELEVEL'] = tools.config.get('pyro_tracelevel',0)
					if tools.config.get('pyro_logfile'):
						settings['PYRO_LOGFILE'] = tools.config.get('pyro_logfile')
					pyrod_ssl = PyroDaemon(tools.config['pyrohost'], pyrossl_port, True, settings)
					pyrod_ssl.start()
	
except Exception, e:
	import traceback
	logger.notifyChannel("web-services", netsvc.LOG_ERROR, "Pyro exception: %s\n%s" % (e, traceback.format_exc()))

tools.config['pyro'] = tools.config.get('pyro', True)
tools.config['pyroport'] = tools.config.get('pyroport', 8071)

if tools.config['pyro']:
	try:
		pyroport = int(tools.config["pyroport"])
	except Exception:
		logger.notifyChannel("init", netsvc.LOG_ERROR, "invalid port '%s'!" % (tools.config["pyroport"]) )
	pyrod = PyroDaemon(tools.config['pyrohost'], pyroport)
	pyrod.start()



# vim:noexpandtab:
