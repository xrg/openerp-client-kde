##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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
from PyQt4.uic import *
import gettext
import copy

import service
import rpc
from common import common
from common import icons

from widget.screen import Screen

class WizardPage(QDialog):
	def __init__(self, arch, fields, state, name, datas, parent=None):
		QDialog.__init__(self, parent)
		self.setWindowTitle( 'Tiny ERP' )
		self.setModal( True )
		buttons = []
		self.datas = datas
		self.buttonsLayout = QHBoxLayout()
		self.buttonsLayout.addStretch()
		print "WizardPage 2"
		for x in state:
			but = QPushButton(x[1])
			# We store the value to return into objectName property
			but.setObjectName(x[0])
			print "STATE: ", x[1]
			# The third element is the gtk-icon
			if len(x) >= 3:
				but.setIcon( icons.kdeIcon( x[2] ) )
			# The forth element is True if the button is the default one
			if len(x) >= 4 and x[3]:
				but.setDefault(True)
			self.buttonsLayout.addWidget(but)
			self.connect( but, SIGNAL('clicked()'), self.slotPush )

		val = {}
		for f in fields:
			if 'value' in fields[f]:
				val[f] = fields[f]['value']

		self.screen = Screen('wizard.'+name, view_type=[], parent=self)
		self.screen.new(default=False)
		self.screen.add_view_custom(arch, fields, display=True)
		# Set default values
		self.screen.current_model.set(val)
		# Set already stored values
		self.screen.current_model.set(self.datas)

		size = self.screen.size()
		self.setMinimumSize( size.width()+20, min(750, size.height()+25) ) 
		self.layout = QVBoxLayout( self )
		self.layout.addWidget( self.screen )
		self.layout.addLayout( self.buttonsLayout )
		self.setWindowTitle(self.screen.current_view.title)
		print "WizardPage 3"
	
	def slotPush( self ):
		o = self.sender()
		self.screen.current_view.store()
		# Get the value we want to return
		button = str( o.objectName() )
		if button != 'end' and not self.screen.current_model.validate():
			self.screen.display()
			return
		self.datas.update(self.screen.get())
		print "slotPush: ", button
		print "slotPush: ", self.datas
		self.result = (button, self.datas)
		self.accept()

class WizardStep( QThread ):
	def __init__( self, wizardId, datas, state, parent=None ):
		QThread.__init__(self, parent)
		self.wizardId = wizardId
		self.datas = datas
		self.state = state
		self.run()

	def run(self):
		print "run 1"
		print "run 2"
		#import options 
		#session = rpc.rpc_session()
		#session.login( options.options['login.login'], 'admin', options.options['login.server'], options.options['login.port'], options.options['login.secure'], options.options['login.db'] )

   		#log_response = rpc.session.login(*res)
		#if log_response==1:
                #options.options['login.server'] = res[2]
                #options.options['login.login'] = res[0]
                #options.options['login.port'] = res[3]
                #options.options['login.secure'] = res[4]
                #options.options['login.db'] = res[5]


		self.result = rpc.session.execute('/wizard', 'execute', self.wizardId, self.datas, self.state, rpc.session.context)
		print "run 3"
		#self.exit()

class Wizard( QObject ):
	def __init__(self, action, datas, state='init', parent=None, context={}):
		QObject.__init__(self, parent)
		if not 'form' in datas:
			datas['form'] = {}
		self.action = action
		self.datas = datas
		self.state = state
		print "BEFORE RPC"
		self.wizardId = rpc.session.execute('/wizard', 'create', self.action)
		print "AFTER RPC: ", self.wizardId
		#self.semaphore = semaphore
		self.finished = False
		self.progress = common.ProgressDialog()
		#self.step()

	def step(self):
		print "step 1"
		if self.state == 'end':
			self.finished = True
			#self.emit( SIGNAL('finished()') )
			#self.semaphore.release()
			return
		print "step 2"
		self.progress.start()
		print "step 3"
		self.wizardStep = WizardStep(self.wizardId, self.datas, self.state, self) 
		print "step 4"
		#self.connect( self.wizardStep, SIGNAL('finished()'), self.finishedStep)
		print "step 5"
		#self.wizardStep.start()
		self.finishedStep()
		print "step 6"

	def finishedStep(self):
		print "finishedStep"
		self.progress.stop()
		print "finishedStep 2"
		res = self.wizardStep.result
		print "finishedStep 3"
		if 'datas' in res:
			self.datas['form'].update( res['datas'] )
		print "finishedStep 4"
		if res['type']=='form':
			#print "finishedStep 5"
			dialog = WizardPage(res['arch'], res['fields'], res['state'], self.action, self.datas['form'])

			#print "finishedStep 6"
			#dialog.screen.current_model.set( self.datas['form'] )
			#print "finishedStep 7"
			if dialog.exec_() == QDialog.Rejected:
				print "finishedStep 8"
				self.finished = True
				return
			print "finishedStep 9"
			(self.state, new_data) = dialog.result
			print "finishedStep 10"
			for d in new_data:
				if new_data[d]==None:
					del new_data[d]
			print "finishedStep 11"
			self.datas['form'].update(new_data)
			print "finishedStep 12"
			del new_data
			#del dialog
			print "finishedStep 13"
		elif res['type']=='action':
			obj = service.LocalService('action.main')
			obj._exec_action(res['action'],self.datas)
			self.state = res['state']
		elif res['type']=='print':
			obj = service.LocalService('action.main')
			self.datas['report_id'] = res.get('report_id', False)
			if res.get('get_id_from_action', False):
				backup_ids = self.datas['ids']
				self.datas['ids'] = self.datas['form']['ids']
				win = obj.exec_report(res['report'], self.datas)
				self.datas['ids'] = backup_ids
			else:
				win = obj.exec_report(res['report'], self.datas)
			self.state = res['state']
		elif res['type']=='state':
			self.state = res['state']
		print "finishedStep 14"
		self.step()
		print "finishedStep 15"

def execute(action, datas, state='init', parent=None, context={}):
	w = Wizard(action, datas, state, parent, context)
	w.step()
	while not w.finished:
		QCoreApplication.processEvents()

	
#def execute(action, datas, state='init'):
	#if not 'form' in datas:
		#datas['form'] = {}
	#wiz_id = rpc.session.execute('/wizard', 'create', action)
	#while state!='end':
		#progress=common.ProgressDialog()
		#progress.start()
		#try:
			#res = rpc.session.execute('/wizard', 'execute', wiz_id, datas, state, rpc.session.context)
		#finally:
			#progress.stop()
		##res = executeWizardStep( wiz_id, datas, state, rpc.session.context )
		#if 'datas' in res:
			#datas['form'].update( res['datas'] )
		#if res['type']=='form':
			#dialog = WizardPage(res['arch'], res['fields'], res['state'], action, datas['form'])
			#dialog.screen.current_model.set( datas['form'] )
			#if dialog.exec_() == QDialog.Rejected:
				#break
			#(state, new_data) = dialog.result
			#for d in new_data:
				#if new_data[d]==None:
					#del new_data[d]
			#datas['form'].update(new_data)
			#del new_data
		#elif res['type']=='action':
			#obj = service.LocalService('action.main')
			#obj._exec_action(res['action'],datas)
			#state = res['state']
		#elif res['type']=='print':
			#obj = service.LocalService('action.main')
			#datas['report_id'] = res.get('report_id', False)
			#if res.get('get_id_from_action', False):
				#backup_ids = datas['ids']
				#datas['ids'] = datas['form']['ids']
				#win = obj.exec_report(res['report'], datas)
				#datas['ids'] = backup_ids
			#else:
				#win = obj.exec_report(res['report'], datas)
			#state = res['state']
		#elif res['type']=='state':
			#state = res['state']

