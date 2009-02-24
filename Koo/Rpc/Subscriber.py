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

from PyQt4.QtCore import *
from time import sleep

class Subscriber(QThread):
	hasSubscriptionModule = True

	def __init__(self, session, parent=None):
		QThread.__init__(self, parent)
		self.session = session.copy()
		self.slot = None

	def subscribe(self, expression, slot = None):
		if not Subscriber.hasSubscriptionModule:
			return
		self.expression = expression
		self.slot = slot
		if self.slot:
			self.connect( self, SIGNAL('published()'), self.slot )
		self.start()

	def unsubscribe(self):
		if not Subscriber.hasSubscriptionModule:
			return
		if self.slot:
			self.disconnect( self, SIGNAL('published()'), self.slot )
		self.terminate()

	def run(self):
		while True:
			try:
				self.result = self.session.call( '/subscription', 'wait', self.expression )
				self.emit( SIGNAL('published()') )
			except Exception, err:
				sleep( 60 )
