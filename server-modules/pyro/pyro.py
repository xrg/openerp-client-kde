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

logger = netsvc.Logger()

class PyroDaemon(Thread):
	def __init__(self, port, ssl=False):
		Thread.__init__(self)
		self.__port = port
		self.__ssl = ssl

	def run(self):
		class RpcDispatcher(Pyro.core.ObjBase):
			def dispatch(self, obj, methodName, *args):
				service=netsvc.LocalService(obj)
				method=getattr(service,methodName)
				service._service._response=None
				result=method(*args)
				if service._service._response!=None:
					result = service._service._response
				return result

		Pyro.core.initServer(storageCheck=0)
		try:
			if self.__ssl:
				a = '/opt/Pyro-3.9.1/examples/ssl/certs'
				Pyro.config.PYROSSL_CERTDIR = a
				Pyro.config.PYROSSL_POSTCONNCHECK = 0
				#Pyro.config.PYROSSL_SERVER_CERT =
				#Pyro.config.PYROSSL_CA_CERT =
				#Pyro.config.PYROSSL_CLIENT_CERT = 
				Pyro.config.PYRO_TRACELEVEL=3
				Pyro.config.PYRO_LOGFILE='/tmp/server_log'
				daemon=Pyro.core.Daemon(port=self.__port,prtcol='PYROSSL')
			else:
				daemon=Pyro.core.Daemon(port=self.__port)
			uri=daemon.connectPersistent( RpcDispatcher(), "rpc" )
			logger.notifyChannel("web-services", netsvc.LOG_INFO, "starting Pyro services, port %s" % self.__port)
			daemon.requestLoop()
		except Exception, e:
			import traceback
			logger.notifyChannel("web-services", netsvc.LOG_ERROR, "Pyro exception: %s\n%s" % (e, traceback.format_exc()))
			raise


tools.config['pyro-ssl'] = tools.config.get('pyro-ssl', False)

if tools.config['pyro-ssl']:
	try:
		import M2Crypto
		tools.config['pyroport-ssl'] = tools.config.get('pyroport-ssl', 8072)
	except ImportError:
		tools.config['pyro-ssl'] =  False
	else:
		try:
			pyroport_ssl = int(tools.config["pyroport-ssl"])
		except Exception:
			logger.notifyChannel("init", netsvc.LOG_ERROR, "invalid ssl port '%s'!" % (tools.config["pyroport-ssl"]) )
		pyrod_ssl = PyroDaemon(pyroport_ssl,tools.config['pyro-ssl'])
		pyrod_ssl.start()

tools.config['pyro'] = tools.config.get('pyro', True)
tools.config['pyroport'] = tools.config.get('pyroport', 8071)

if tools.config['pyro']:
	try:
		pyroport = int(tools.config["pyroport"])
	except Exception:
		logger.notifyChannel("init", netsvc.LOG_ERROR, "invalid port '%s'!" % (tools.config["pyroport"]) )
	pyrod = PyroDaemon(pyroport)
	pyrod.start()



# vim:noexpandtab:
