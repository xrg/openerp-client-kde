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
	def __init__(self, port):
		Thread.__init__(self)
		self.__port = port

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
		daemon=Pyro.core.Daemon(port=self.__port)
		uri=daemon.connectPersistent( RpcDispatcher(), "rpc" )
		logger.notifyChannel("web-services", netsvc.LOG_INFO, "starting Pyro services, port %s" % self.__port)
		daemon.requestLoop()


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
