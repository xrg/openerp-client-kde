##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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
from PyQt4.QtGui import *
from Common.Ui import *

from Koo import Rpc
from Koo.Common import Api
from Koo.Common import Common
from Koo.Common import Icons

from Koo.Screen.Screen import Screen
from Koo.Model.Group import RecordGroup
import logging

## @brief The WizardPage class shows a QDialog with the information givenin one wizard step.
class WizardPage(QDialog):
	def __init__(self, arch, fields, state, name, datas, parent=None):
		QDialog.__init__(self, parent)
		self.setModal( True )
		buttons = []
		self.datas = datas
		self.buttonsLayout = QHBoxLayout()
		self.buttonsLayout.addStretch()
		for x in state:
			but = QPushButton( Common.normalizeLabel( x[1] ) )
			# We store the value to return into objectName property
			but.setObjectName(x[0])
			# The third element is the gtk-icon
			if len(x) >= 3:
				but.setIcon( Icons.kdeIcon( x[2] ) )
			# The forth element is True if the button is the default one
			if len(x) >= 4 and x[3]:
				but.setDefault(True)
			self.buttonsLayout.addWidget(but)
			self.connect( but, SIGNAL('clicked()'), self.slotPush )

		val = {}
		for f in fields:
			if 'value' in fields[f]:
				val[f] = fields[f]['value']

		self.group = RecordGroup( 'wizard.'+name )
		# Do not allow record loading as most probably 'wizard.'+name model
		# won't exist in the server
		self.group.setDomainForEmptyGroup()
		self.screen = Screen( self )
		self.screen.setRecordGroup( self.group )
		self.screen.new(default=False)
		self.screen.addView(arch, fields, display=True)
		# Set default values
		self.screen.currentRecord().set(val)
		# Set already stored values
		self.screen.currentRecord().set(self.datas)
		self.screen.display()

		# Set minimum and maximum dialog size
		size = self.screen.sizeHint()
		self.setMinimumSize( size.width()+100, min(600, size.height()+25) ) 
		size = QApplication.desktop().availableGeometry( self ).size()
		size -= QSize( 50, 50 )
		self.setMaximumSize( size )

		self.layout = QVBoxLayout( self )
		self.layout.addWidget( self.screen )
		self.layout.addLayout( self.buttonsLayout )
		self.setWindowTitle(self.screen.currentView().title)
	
	def slotPush( self ):
		o = self.sender()
		self.screen.currentView().store()
		# Get the value we want to return
		button = str( o.objectName() )
		if button != 'end' and not self.screen.currentRecord().validate():
			self.screen.display()
			return
		self.datas.update(self.screen.get())
		self.result = (button, self.datas)
		self.accept()

## @brief The Wizard class shows a step by step wizard with the provided information.
class Wizard( QObject ):
	def __init__(self, action, datas, state='init', parent=None, context=None):
		QObject.__init__(self, parent)
		if context is None:
			context = {}
		if not 'form' in datas:
			datas['form'] = {}
		self.action = action
		self.datas = datas
		self.state = state
		self.context = context
		self.wizardId = Rpc.session.execute('/wizard', 'create', self.action)
		self.finished = False
		self.progress = Common.ProgressDialog( QApplication.activeWindow() )
		self.thread = None
		self.context = context
		self._log = logging.getLogger('koo.wizard')

	def step(self):
		if self.state == 'end':
			self.finished = True
			return
		self.progress.start()
		QApplication.setOverrideCursor( Qt.WaitCursor )
		ctx = self.context.copy()
		ctx.update(Rpc.session.context)
		self._log.debug("Wizard step with context: %r" % ctx)
		self.thread = Rpc.session.executeAsync( self.finishedStep, '/wizard', 'execute', self.wizardId, self.datas, self.state, ctx )

	def finishedStep(self, res, exception):
		self.progress.stop()
		QApplication.restoreOverrideCursor()
		
		# Check if 'res' is None as it can happen with 'Split in production lots'
		# in inventory 'Movements', for example, if no production sequence is defined.
		# We'll also leave the wizard if an exception was thrown.
		if exception or not res:
			self.state = 'end'
			self.step()
			return

		ctx = self.context.copy()
		ctx.update(Rpc.session.context)
		self._log.debug("Wizard finish step with context: %r" % ctx)

		if 'datas' in res:
			self.datas['form'].update( res['datas'] )
		if res['type']=='form':
			dialog = WizardPage(res['arch'], res['fields'], res['state'], self.action, self.datas['form'])

			if dialog.exec_() == QDialog.Rejected:
				self.finished = True
				return
			(self.state, new_data) = dialog.result

			for d in new_data.keys():
				if new_data[d]==None:
					del new_data[d]
			self.datas['form'].update(new_data)
			del new_data
		elif res['type']=='action':
			Api.instance.executeAction(res['action'],self.datas)
			self.state = res['state']
		elif res['type']=='print':
			self.datas['report_id'] = res.get('report_id', False)
			if res.get('get_id_from_action', False):
				backup_ids = self.datas['ids']
				self.datas['ids'] = self.datas['form']['ids']
				win = Api.instance.executeReport(res['report'], self.datas, ctx)
				self.datas['ids'] = backup_ids
			else:
				win = Api.instance.executeReport(res['report'], self.datas, ctx)
			self.state = res['state']
		elif res['type']=='state':
			self.state = res['state']
		self.step()

## @brief Executes the wizard with the provided information.
## 
## We assume the Wizard object will behave as a thread, all its long operations
## will be done asynchronously. Thus, we install a timer in our event loop to
## check for wizard finish
def execute(action, datas, state='init', parent=None, context=None):
	if context is None:
		context = {}
	w = Wizard(action, datas, state, parent, context)
	w.step()
	timer = QTimer(QCoreApplication.instance())
	timer.setSingleShot(False)
	# this timer won't call anything! Just cause the event loop to have
	# events every 0.5 sec
	timer.start(500)
	while not w.finished:
		QCoreApplication.processEvents(QEventLoop.WaitForMoreEvents)
	timer.stop()
	

