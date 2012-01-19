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

from PyQt4.QtCore import QThread, SIGNAL
from time import sleep
import logging
from Rpc import RpcServerException

## @brief The Subscriber class provides a mechanisme for subscribing to server events.
#
# In order to use this class effectively you'll need the koo module installed on the server.
# This module adds a new /subscription service. You can use this class in conjunction with
# your own server modules which can publish events. By default, the koo module already publishes
# events on any update/create/delete operation on a model.
# 
# If the 'koo' module is not installed the Subscription service won't emit any signals, but won't
# return any errors either.
#
# Example of usage:
#
# self.subscriber = Rpc.Subscriber(Rpc.session, self)
# self.subscriber.subscribe( 'updated_model:res.request', self.updateRequestsStatus )
#
# This example will emit a signal (call self.updateRequestsStatus) each time a changed occurs
# on any record in 'res.request' model.

class Subscriber(QThread):
	## @brief Creates a new Subscriber object from the given session and with 'parent' as QObject parent.
	def __init__(self, session, parent=None):
		QThread.__init__(self, parent)
		self.session = session
		self.slot = None

	## @brief Subscribes to the given 'expression' event on the server. And calls 'slot' each
	# time the given event is published.
	def subscribe(self, expression, slot = None):
		self.expression = expression
		self.slot = slot
		if self.slot:
			self.connect( self, SIGNAL('published()'), self.slot )
		self.start()

	## @brief Unsubscribes from the previously subscribed event.
	#
	# If subscribe() wasn't previously called, nothing happens.
	def unsubscribe(self):
		if self.slot:
			self.disconnect( self, SIGNAL('published()'), self.slot )
		self.terminate()

	def run(self):
                logger = logging.getLogger('Koo.Subscriber')
		while True:
			try:
				self.result = self.session.call( '/subscription', 'wait', (self.expression,), notify=False)
				if self.result:
					self.emit( SIGNAL('published()') )
				else:
					logger.warning("cannot subscribe to %s, waiting 5min", self.expression)
					sleep(300)
                        except RpcServerException, e:
                            print e.code, e.type, e.args
                            if e.code == 'subscription':
                                logger.warning("Server does not support subscriptions")
                                break
                            else:
                                logger.error("Server exception: %s", e)
                                sleep(120)
			except Exception, err:
                                logger.exception("Exception:")
				sleep( 60 )

#eof
