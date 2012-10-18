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

from Koo.Common.Ui import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from Koo import Rpc
from Koo.Common import Common
from Koo.Common.Settings import Settings

from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup

import logging

(ScreenDialogUi, ScreenDialogBase) = loadUiType( Common.uiPath('screen_dialog.ui') ) 

class ScreenDialog( QDialog, ScreenDialogUi ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		ScreenDialogUi.__init__( self )
		self.setupUi( self )

		self.setMinimumWidth( 800 )
		self.setMinimumHeight( 600 )

		self.connect( self.pushOk, SIGNAL("clicked()"), self.accepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.rejected )
		self.group = None
		self.record = None
		self.recordId = None
		self.model = None
		self._recordAdded = False
		self._context = {}
		self._domain = []
		self.devel_mode = Settings.value("client.devel_mode", False)
		if self.devel_mode:
			self.connect( self.pushDevInfo, SIGNAL("clicked()"),self.showLogs)
		else:
			self.pushDevInfo.hide()

	def setup(self, model, id=None):
		if self.group:
			return
		self.group = RecordGroup( model, context=self._context )
		self.model = model
		self.group.setDomain( self._domain )
		self.screen = Screen(self)
		self.screen.setRecordGroup( self.group )
		self.screen.setViewTypes( ['form'] )
		if id:
			self._recordAdded = False 
			self.screen.load([id])
		else:
			self._recordAdded = True
			self.screen.new()
		self.screen.display()
		self.layout().insertWidget( 0, self.screen  )
		self.screen.show()

	def setAttributes(self, attrs):
		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( unicode(self.windowTitle()) + ' - ' + attrs['string'])

	def setContext(self, context):
		self._context = context

	def setDomain(self, domain):
		self._domain = domain

	def rejected( self ):
		if self._recordAdded:
			self.screen.remove()
		self.reject()

	def accepted( self ):
		self.screen.currentView().store()

		if self.screen.save():
			self.record = self.screen.currentRecord().name()
			self.recordId = self.screen.currentRecord().id
			self.accept()
	
	def showLogs(self):
		id = self.screen.currentId()
		if not (id or self.devel_mode):
			self.updateStatus(_('You have to select one resource!'))
			return False
		if id:
			res = Rpc.session.execute('/object', 'execute', self.model, 'perm_read', [id])
		else:
			res = []
		message = u''
		if self.devel_mode:
			message = "Object: %s\n" %(self.model)
			message += "Domain: %s\nContext: %s\n" %(self._domain, self._context)
			message += "Scr context: %s\n" % (self.screen.context)
			message += "\n"

		todo = [
			('id', _('ID')),
			('str_id', _('Model ID')),
			('create_uid', _('Creation User')),
			('create_date', _('Creation Date')),
			('write_uid', _('Latest Modification by')),
			('write_date', _('Latest Modification Date')),
		]

		for line in res:
			line['str_id'] = None
			try:
				# Using call() because we don't want exception handling
				res2 = Rpc.session.call('/object', 'execute',
					('ir.model.data', 'get_rev_ref', self.model, line['id']), notify=False)
				
				if res2 and res2[1]:
					line['str_id'] = ', '.join(res2[1])
			except AttributeError:
				pass
			except Exception, e:
				# This can happen, just because old servers don't have
				# this method.
				log = logging.getLogger('koo.screen')
				log.exception("Cannot rev ref id:")
		
			for (key,val) in todo:
				if not key in line:
				    continue
				if line[key] and key in ('create_uid','write_uid') \
				    and isinstance(line[key], (tuple, list)):
					line[key] = line[key][1]
				message += val + ': ' + unicode(line[key] or '-') + '\n'
		QMessageBox.information(self, _('Record log'), message)

