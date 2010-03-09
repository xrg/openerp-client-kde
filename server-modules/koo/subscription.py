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

from threading import Thread, Semaphore, Lock
import netsvc
from service.web_services import baseExportService
import time
from workflow.wkf_service import workflow_service
import SimpleXMLRPCServer
from service import security

class new_workflow_service(workflow_service):
	def __init__(self, name='workflow', audience='*'):
		workflow_service.__init__(self, name, audience)
	
	def trg_create(self, uid, res_type, res_id, cr):
		netsvc.LocalService('subscription').publish( 'updated_model:%s' % res_type )
		return workflow_service.trg_create(self, uid, res_type, res_id, cr)

	def trg_write(self, uid, res_type, res_id, cr):
		netsvc.LocalService('subscription').publish( 'updated_model:%s' % res_type )
		return workflow_service.trg_write(self, uid, res_type, res_id, cr)

	def trg_delete(self, uid, res_type, res_id, cr):
		netsvc.LocalService('subscription').publish( 'updated_model:%s' % res_type )
		return workflow_service.trg_delete(self, uid, res_type, res_id, cr)
# new_workflow_service()

class subscription_services(baseExportService):
	_auth_commands = { 'db': ['wait' ], }
	def __init__(self, name="subscription"):
		baseExportService.__init__(self,name)
		self.joinGroup('web-services')
		#self.exportMethod(self.wait)
		#self.exportMethod(self.publish)
		self.subscriptions = []
		self.connections = {}
		self.lock = Lock()
		self.queue = []
		self.waits = []
		
	def dispatch(self, method, auth, params):
		(db, uid, passwd ) = params[0:3]
		params = params[3:]
		if method not in ['wait']:
			raise KeyError("Method not supported %s" % method)
		security.check(db,uid,passwd)
		fn = getattr(self, 'exp_'+method)
		res = fn(db, uid, *params)
		return res

	def exp_wait(self, db, uid, expression):
		self.lock.acquire()
		currentLock = Semaphore(0)
		self.waits.append( {'expression': expression, 'lock': currentLock } )
		self.lock.release()
		currentLock.acquire()
		# Ensure we don't reply too fast when client and server are on the same
		# machine
		time.sleep(0.3)

	def publish(self, expression):
		self.lock.acquire()
		waits = self.waits[:]
		remove = []
		for wait in waits:
			if wait['expression'] == expression:
				wait['lock'].release()
				self.waits.remove( wait )
		self.lock.release()

	def connection(self, host):
		if host in connections:
			data = connections[host]
			return Pyro.core.getProxyForURI( 'PYROLOC://%s:%s' % ( data['host'], data['port'] ) )
		self.proxy = Pyro.core.getProxyForURI( self.url )
		
		
subscription_services()

