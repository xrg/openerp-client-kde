##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007-2009 Albert Cervera i Areny <albert@nan-tic.com>
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

import types
import gettext

from Koo import Rpc
from SearchDialog import *
from ExportDialog import *
from ImportDialog import *
from AttachmentDialog import *
from GoToIdDialog import *
from MassiveUpdateDialog import *

from Koo.Common import Api
from Koo.Common import Common
from Koo.Common.Settings import *
import copy

from Koo.Screen.Screen import *
from Koo.Model.Group import RecordGroup
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(FormWidgetUi, FormWidgetBase) = loadUiType( Common.uiPath('formcontainer.ui') )

class FormWidget( QWidget, FormWidgetUi ):
	# form constructor:
	# model -> Name of the model the form should handle
	# res_id -> List of ids of type 'model' to load
	# domain -> Domain the models should be in
	# view_type -> type of view: form, tree, graph, calendar, ...
	# view_ids -> Id's of the views 'ir.ui.view' to show
	# context -> Context for the current data set
	# parent -> Parent widget of the form
	# name -> User visible title of the form
	def __init__(self, model, res_id=False, domain=[], view_type=None, view_ids=[], context={}, parent=None, name=False):
		QWidget.__init__(self,parent)
		FormWidgetUi.__init__(self)
		self.setupUi( self )

		if not view_type:
			view_type = ['form','tree']
		else:
			if view_type[0] in ['graph'] and not res_id:
				res_id = Rpc.session.execute('/object', 'execute', model, 'search', domain)
		fields = {}
		self.model = model
		self.previousAction = None
		self.fields = fields
		self.domain = domain
		self.context = context
		self.viewTypes = view_type
		self.viewIds = view_ids

		self._switchViewMenu = QMenu( self )
		self._viewActionGroup = QActionGroup( self )
		self._viewActionGroup.setExclusive( True )
		for view in self.viewTypes:
			action = ViewFactory.viewAction( view, self )
			if not action:
				continue
			self.connect( action, SIGNAL('triggered()'), self.switchView )
			self._switchViewMenu.addAction( action )
			self._viewActionGroup.addAction( action )

		self.group = RecordGroup( self.model, context=self.context )
		self.group.setDomain( domain )
		self.connect(self.group, SIGNAL('modified()'), self.notifyRecordModified)

		self.screen.setRecordGroup( self.group )
		self.screen.setEmbedded( False )
		self.connect( self.screen, SIGNAL('activated()'), self.switchView )
		self.connect( self.screen, SIGNAL('currentChanged()'), self.updateStatus )
		self.connect( self.screen, SIGNAL('closed()'), self.closeWidget )
		self.connect( self.screen, SIGNAL('recordMessage(int,int,int)'), self.updateRecordStatus )
		self.connect( self.screen, SIGNAL('statusMessage(QString)'), self.updateStatus )

		self._allowOpenInNewWindow = True

		# Remove ids with False value
		self.screen.setupViews( view_type, view_ids )


		if name:
			self.name = name
		else:
			self.name = self.screen.currentView().title

		self.handlers = {
			'New': self.new,
			'Save': self.save,
			'Export': self.export,
			'Import': self.import_,
			'Delete': self.remove,
			'Find': self.search,
			'Previous': self.previous,
			'Next':  self.next,
			'GoToResourceId':  self.goto,
			'AccessLog':  self.showLogs,
			'Reload': self.reload,
			'Switch': self.switchView,
			'Attach': self.showAttachments,
			'Duplicate': self.duplicate,
			'MassiveUpdate': self.massiveUpdate
		}

		if res_id:
			if isinstance(res_id, int):
				res_id = [res_id]
			self.screen.load(res_id)
		else:
			if len(view_type) and view_type[0]=='form':
				self.screen.new()

		self.updateSwitchView()

		self.reloadTimer = QTimer(self)
		self.connect( self.reloadTimer, SIGNAL('timeout()'), self.autoReload )
		self.pendingReload = False

		# We always use the Subscriber as the class itself will handle
		# whether the module exists on the server or not
		self.subscriber = Rpc.Subscriber(Rpc.session, self)
		if Settings.value('auto_reload'):
			self.subscriber.subscribe( 'updated_model:%s' % model, self.autoReload )

	def notifyRecordModified(self):
		self.updateStatus( _('<font color="blue">Document modified</font>') )

	## @brief Establishes that every value seconds a reload should be scheduled.
	# If value is < 0 only Subscription based reloads are executed. Note that if
	# value is != 0 Subscription based reloads are always used if available.
	def setAutoReload(self, value):
		if value:
			# We use both, timer and subscriber as in some cases information may change
			# only virtually: Say change the color of a row depending on current time.
			# If the value is negative we don't start the timer but keep subscription,
			# so this allows setting -1 in autorefresh when you don't want timed updates
			# but only when data is changed in the server.
			if value > 0:
				self.reloadTimer.start( int(value) * 1000 )
			if not Settings.value('auto_reload'):
				# Do not subscribe again if that was already done in the constructor
				self.subscriber.subscribe( 'updated_model:%s' % self.model, self.autoReload )
		else:
			self.reloadTimer.stop()

	def setAllowOpenInNewWindow( self, value ):
		self._allowOpenInNewWindow = value

	def goto(self):
		if not self.modifiedSave():
			return
		dialog = GoToIdDialog( self )
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.load( [dialog.result] )
		
	def setStatusBarVisible(self, value):
		self.uiStatusLabel.setVisible( value )
		self.uiStatus.setVisible( value )
		self.uiRecordStatus.setVisible( value )
		
	def showAttachments(self):
		id = self.screen.currentId()
		if id:
			if Settings.value('attachments_dialog'):
				QApplication.setOverrideCursor( Qt.WaitCursor )
				try:
					window = AttachmentDialog(self.model, id, self)
					self.connect( window, SIGNAL('destroyed()'), self.attachmentsClosed )
				except Rpc.RpcException, e:
					QApplication.restoreOverrideCursor()
					return
				QApplication.restoreOverrideCursor()
				window.show()
			else:
				context = self.context.copy()
				context.update(Rpc.session.context)
				action = Rpc.session.execute('/object', 'execute', 'ir.attachment', 'action_get', context)
				action['domain'] = [('res_model', '=', self.model), ('res_id', '=', id)]
				context['default_res_model'] = self.model
				context['default_res_id'] = id
				Api.instance.executeAction( action, {}, context )
		else:
			self.updateStatus(_('No resource selected !'))

	def attachmentsClosed(self):
		self.updateStatus()

	def switchView(self):
		if not self.modifiedSave():
			return
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			if ( self._allowOpenInNewWindow and QApplication.keyboardModifiers() & Qt.ControlModifier ) == Qt.ControlModifier:
				if QApplication.keyboardModifiers() & Qt.ShiftModifier:
					target = 'background'
				else:
					target = 'current'
				Api.instance.createWindow( None, self.model, self.screen.currentId(), 
					view_type='form', mode='form,tree', target=target)
			else:
				sender = self.sender()
				name = unicode( sender.objectName()  )
				if isinstance(sender, QAction) and name != 'actionSwitch':
					self.sender().setChecked( True )
					self.screen.switchView( name )
				else:
					self.screen.switchView()
			if self.pendingReload:
				self.reload()
			self.updateSwitchView()
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def showLogs(self):
		id = self.screen.currentId()
		if not id:
			self.updateStatus(_('You have to select one resource!'))
			return False
		res = Rpc.session.execute('/object', 'execute', self.model, 'perm_read', [id])
		message = ''
		for line in res:
			todo = [
				('id', _('ID')),
				('create_uid', _('Creation User')),
				('create_date', _('Creation Date')),
				('write_uid', _('Latest Modification by')),
				('write_date', _('Latest Modification Date')),
			]
			for (key,val) in todo:
				if line[key] and key in ('create_uid','write_uid'):
					line[key] = line[key][1]
				message += val + ': ' + str(line[key] or '-') + '\n'
		QMessageBox.information(self, _('Record log'), message)

	def remove(self):
		value = QMessageBox.question(self,_('Question'),_('Are you sure you want to remove these records?'),QMessageBox.Yes|QMessageBox.No)
		if value == QMessageBox.Yes:
			QApplication.setOverrideCursor( Qt.WaitCursor )
			try: 
				if not self.screen.remove(unlink=True):
					self.updateStatus(_('Resource not removed !'))
				else:
					self.updateStatus(_('Resource removed.'))
			except Rpc.RpcException, e:
				pass
			QApplication.restoreOverrideCursor()

	def import_(self):
		fields = []
		dialog = ImportDialog(self.model, self.screen.fields, fields)
		dialog.exec_()
		if not self.screen.isModified():
			self.reload()

	def export(self):
		fields = []
		dialog = ExportDialog(self.model, self.screen.selectedIds(), self.screen.fields, fields)
		dialog.exec_()

	def new(self):
		if not self.modifiedSave():
			return
		self.screen.new()
	
	def duplicate(self):
		if not self.modifiedSave():
			return
		res_id = self.screen.currentId()
		new_id = Rpc.session.execute('/object', 'execute', self.model, 'copy', res_id, {}, Rpc.session.context)
		self.screen.load( [new_id], self.screen.addOnTop() )
		self.updateStatus(_('<font color="orange">Working now on the duplicated document</font>'))

	def save(self):
		if not self.screen.currentRecord():
			return
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			modification = self.screen.currentRecord().id
			id = self.screen.save()
			if id:
				self.updateStatus(_('<font color="green">Document saved</font>'))
				if not modification and Settings.value('auto_new'):
					self.screen.new()
			else:
				self.updateStatus(_('<font color="red">Invalid form</font>'))
		except Rpc.RpcException, e:
			id = False
		QApplication.restoreOverrideCursor()
		return bool(id)

	def previous(self):
		if not self.modifiedSave():
			return
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.screen.displayPrevious()
			self.updateStatus()
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def next(self):
		if not self.modifiedSave():
			return
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.screen.displayNext()
			self.updateStatus()
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def autoReload(self):
		# Do not reload automatically if it's an editable list
		# By explicitly disallowing this it makes the global 
		# koo module auto_reload option to be usable.
		if self.screen.currentView().showsMultipleRecords() and not self.screen.currentView().isReadOnly():
			return
		# Do not reload automatically if there are any modified records
		# However, we take note that there's a pending reload which 
		# will be done in the next switchView()
		if self.screen.isModified():
			self.pendingReload = True
			return
		self.reload()
		# If current view only shows one record self.screen.reload() 
		# only reloads the current record. As we want to be sure that
		# any new records will appear in the list view (or any view that 
		# shows multiple records), we set pendingReload to be run
		# when switching view.
		if not self.screen.currentView().showsMultipleRecords():
			self.pendingReload = True

	def reload(self):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.screen.reload()
			self.updateStatus()
			self.pendingReload = False
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def cancel(self):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			self.screen.cancel()
			self.updateStatus()
		except Rpc.RpcException, e:
			pass
		QApplication.restoreOverrideCursor()

	def search(self):
		if not self.modifiedSave():
			return
		dom = self.domain
		dialog = SearchDialog(self.model, domain=self.domain, context=self.context, parent=self)
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.clear()
		self.screen.load( dialog.result )

	def updateStatus(self, message=''):
		if self.model and self.screen.currentRecord() and self.screen.currentRecord().id:
			ids=Rpc.session.execute('/object', 'execute', 'ir.attachment', 'search', [('res_model','=',self.model),('res_id','=',self.screen.currentRecord().id)])
		else:
			ids = []
		message = ( _("(%s attachments) ") % len(ids) ) + message
		self.uiStatus.setText( message )

	def updateSwitchView(self):
		for action in self._viewActionGroup.actions():
			if action.objectName() == self.screen.currentView().viewType():
				action.setChecked( True )
				break

	def updateRecordStatus(self, position, count, value):
		if not count:
			msg = _('No records')
		else:
			pos = '_'
			if position >= 0:
				pos = str(position+1)
			if value == None:
				# Value will be None only when it's called by the constructor
				edit = _('No document selected')
			else:
				# Other times it'll either be 0 (new document) or the appropiate
				# object i
				edit = _('New document')
				if value > 0:
					edit = _('Editing document (id: %s)') % str(value)
			msg = _('Record: %(name)s / %(count)s - %(name2)s') % { 'name': pos, 'count': str(count), 'name2': edit }

		self.uiRecordStatus.setText( msg )

	def modifiedSave(self):
		if self.screen.isModified():
			value = QMessageBox.question( self, _('Question'), _('This record has been modified do you want to save it?'), QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel )
			if value == QMessageBox.Save:
				return self.save()
			elif value == QMessageBox.Discard:
				self.cancel()
				return True
			else:
				return False
		else:
			# If a new record was created but not modified, isModified() will return
			# False but we want to cancel new records anyway.
			# We call screen.cancel() directly as we don't want to trigger an updateStatus()
			# which will result in a server request.
			self.screen.cancel()
		return True

	def massiveUpdate(self):
		if not self.screen.selectedIds():
			QMessageBox.information( self, _('No records selected'), _('No records selected') )
			return
		dialog = MassiveUpdateDialog( self )
		dialog.setIds( self.screen.selectedIds() )
		dialog.setModel( self.model )
		dialog.setContext( self.context )
		dialog.setup( self.viewTypes, self.viewIds )
		dialog.exec_()
		self.reload()

	def closeWidget(self):
		self.screen.storeViewSettings()
		self.reloadTimer.stop()
		self.subscriber.unsubscribe()
		self.emit( SIGNAL('closed()') )

	def canClose(self, urgent=False):
		# Store settings of all opened views before closing the tab.
		self.screen.storeViewSettings()
		if self.modifiedSave():
			# Here suppose that if we return True the form/tab will
			# actually be closed, so stop reload timer so it doesn't
			# remain active if the object is freed.
			self.reloadTimer.stop()
			self.subscriber.unsubscribe()
			return True
		else:
			return False

	def actions(self):
		return self.screen.actions

	def switchViewMenu(self):
		return self._switchViewMenu

	def __del__(self):
		print "DEL FORMWIDGET"
		self.group.__del__()
		del self.group

