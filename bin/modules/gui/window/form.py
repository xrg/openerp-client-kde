##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: form.py 4444 2006-11-05 11:12:27Z pinky $
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

import rpc
import win_preference
import win_search
import win_export
import win_import

from common import common
import service
import options
import copy

import gc

from widget.screen import Screen
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from win_gotoid import *


class form( QWidget ):
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
		loadUi( common.uiPath('formcontainer.ui'), self ) 

		if not view_type:
			view_type = ['form','tree']
		else:
			if view_type[0] in ['tree','graph'] and not res_id:
				res_id = rpc.session.execute('/object', 'execute', model, 'search', domain)

		fields = {}
		self.model = model
		self.previous_action = None
		self.fields = fields
		self.domain = domain
		self.context = context

		self.screen = Screen(self.model, view_type=view_type, context=self.context, view_ids=view_ids, domain=domain, parent=self)
		self.screen.setEmbedded( False )
		self.connect(self.screen, SIGNAL('recordMessage(int,int,int)'), self._recordMessage)
		if name:
			self.name = name
		else:
			self.name = self.screen.current_view.title

		# TODO: Use desinger's widget promotion
		self.layout().insertWidget(0, self.screen )

		self.has_backup = False
		self.backup = {}

		self.handlers = {
			'New': self.sig_new,
			'Save': self.sig_save,
			'Export': self.sig_export,
			'Import': self.sig_import,
			'Repeat': self.sig_print_repeat,
			'Delete': self.sig_remove,
			'Find': self.sig_search,
			'Previous': self.sig_previous,
			'Next':  self.sig_next,
			'GoToResourceId':  self.sig_goto,
			'AccessLog':  self.sig_logs,
			'Print': self.sig_print,
			'Reload': self.sig_reload,
			'PrintHtml': self.sig_print_html,
			'Print': self.sig_action,
			'Switch': self.sig_switch,
			'Attach': self.sig_attach,
			'Plugins': self.sig_plugins,
			'Duplicate': self.duplicate
		}
		if res_id:
			if isinstance(res_id, int):
				res_id = [res_id]
			self.screen.load(res_id)
		else:
			if len(view_type) and view_type[0]=='form':
				self.sig_new(autosave=False)
		self.updateStatus()

	def sig_goto(self, *args):
		if not self.modified_save():
			return
		dialog = GoToIdDialog( self )
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.load( [dialog.result] )
		
	def ids_get(self):
		return self.screen.ids_get()

	def id_get(self):
		return self.screen.id_get()

	def _form_action_action(self, name, value):
		id = self.sig_save(sig_new=False)
		if id:
			id2 = value[2] or id
			obj = service.LocalService('action.main')
			action_id = int(value[0])
			obj.execute(action_id, {'model':value[1], 'id': id2, 'ids': [id2]})
			self.sig_reload()

	def _form_action_object(self, name, value):
		id = self.sig_save(sig_new=False, auto_continue=False)
		if id:
			id2 = value[2] or id
			rpc.session.execute('/object', 'execute', value[1], value[0], [id2], rpc.session.context)
			self.sig_reload()

	def _form_action_workflow(self, name, value):
		id = self.sig_save(sig_new=False, auto_continue=False)
		if id:
			rpc.session.execute('/object', 'exec_workflow', value[1], value[0], id)
			self.sig_reload()

	def sig_attach(self, widget=None):
		id = self.screen.id_get()
		if id:
			import win_attach
			win = win_attach.win_attach(self.model, id, self)
			win.show()
			self.updateStatus()
		else:
			self.updateStatus(_('No resource selected !'))

	def sig_switch(self, widget=None, mode=None):
		if not self.modified_save():
			return
		self.screen.switchView()

	def _id_get(self):
		return self.screen.id_get()

	def sig_logs(self, widget=None):
		id = self._id_get()
		if not id:
			self.updateStatus(_('You have to select one resource!'))
			return False
		res = rpc.session.execute('/object', 'execute', self.model, 'perm_read', [id])
		message = ''
		for line in res:
			todo = [
				('id', _('ID')),
				('create_uid', _('Creation User')),
				('create_date', _('Creation Date')),
				('write_uid', _('Latest Modification by')),
				('write_date', _('Latest Modification Date')),
				('uid', _('Owner')),
				('gid', _('Group Owner')),
				('level', _('Access Level'))
			]
			for (key,val) in todo:
				if line[key] and key in ('create_uid','write_uid','uid'):
					line[key] = line[key][1]
				message+=val+': '+str(line[key] or '/')+'\n'
		QMessageBox.information(self, '', message)

	def sig_remove(self):
		value = QMessageBox.question(self,_('Question'),_('Are you sure you want to remove this record?'),QMessageBox.Yes|QMessageBox.No)
		if value == QMessageBox.Yes:
			id = self.screen.remove(unlink=True)
			if not id:
				self.updateStatus(_('Resource not removed !'))
			else:
				self.updateStatus(_('Resource removed.'))

	def sig_import(self):
		fields = []
		dialog = win_import.win_import(self.model, self.screen.fields, fields)
		dialog.exec_()

	def sig_export(self):
		fields = []
		dialog = win_export.win_export(self.model, self.screen.ids_get(), self.screen.fields, fields)
		dialog.exec_()

	def sig_new(self, widget=None, autosave=True):
		if autosave:
			if not self.modified_save():
				return
		self.screen.new()
	
	def duplicate(self):
		if not self.modified_save():
			return
		res_id = self._id_get()
		new_id = rpc.session.execute('/object', 'execute', self.model, 'copy', res_id, {}, rpc.session.context)
		self.screen.load([new_id])
		self.updateStatus(_('Working now on the duplicated document !'))

	def _form_save(self, auto_continue=True):
		pass

	def sig_save(self, widget=None, sig_new=True, auto_continue=True):
		modification = self.screen.current_model.id
		id = self.screen.save_current()
		if id:
			self.updateStatus(_('Document saved !'))
			if not modification:
				self.screen.new()
		else:
			self.updateStatus(_('Invalid form !'))
		return bool(id)

	def sig_previous(self, widget=None):
		if not self.modified_save():
			return
		self.screen.display_prev()
		self.updateStatus()

	def sig_next(self, widget=None):
		if not self.modified_save():
			return
		self.screen.display_next()
		self.updateStatus()

	def sig_reload(self):
		if self.screen.current_view.view_type == 'form':
			self.screen.cancel_current()
			self.screen.display()
		else:
			id = self.screen.id_get()
			ids = self.screen.ids_get()
			self.screen.clear()
			self.screen.load(ids)
			for model in self.screen.models:
				if model.id == id:
					self.screen.current_model = model
					self.screen.display()
					break
		self.updateStatus()

	def sig_action(self, keyword='client_action_multi', previous=False, report_type='pdf', adds={}):
		ids = self.screen.ids_get()
		if self.screen.current_model:
			id = self.screen.current_model.id
		else:
			id = False
		if self.screen.current_view.view_type == 'form':
			id = self.screen.save_current()
			if not id:
				return False
			ids = [id]
		if len(ids):
			obj = service.LocalService('action.main')
			if previous and self.previous_action:
				obj._exec_action(self.previous_action[1], {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type})
			else:
				res = obj.exec_keyword(keyword, {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type}, adds=adds)
				if res:
					self.previous_action = res
			self.sig_reload()
		else:
			self.updateStatus(_('No record selected!'))

	def sig_print_repeat(self):
		self.sig_action('client_print_multi', True)

	def sig_print_html(self):
		self.sig_action('client_print_multi', report_type='html')

	def sig_print(self):
		self.sig_action('client_print_multi', adds={'Print Screen': {'report_name':'printscreen.list', 'name':'Print Screen', 'type':'ir.actions.report.xml'}})

	def sig_search(self, widget=None):
		if not self.modified_save():
			return
		dom = self.domain
		dialog = win_search.win_search(self.model, domain=self.domain, context=self.context, parent=self)
		if dialog.exec_() == QDialog.Rejected:
			return
		self.screen.clear()
		self.screen.load( dialog.result )

	def updateStatus(self, message=''):
		if self.model and self.screen.current_model and self.screen.current_model.id:
			ids=rpc.session.execute('/object', 'execute', 'ir.attachment', 'search', [('res_model','=',self.model),('res_id','=',self.screen.current_model.id)])
			message = ( _("(%s attachments) ") % len(ids) ) + message
		self.uiStatus.setText( message )

	def _recordMessage(self, position, count, value):
		if not count:
			msg = _('No record selected')
		else:
			name = '_'
			if position >= 0:
				name = str(position+1)
			name2 = _('New document')
			if value:
				name2 = _('Editing document (id: %s)') % str(value)
			msg = _('Record: %s / %s - %s') % ( name, str(count), name2 )

		self.statForm.setText( msg )

	def sig_preference(self, widget=None):
		actions = rpc.session.execute('/object', 'execute', 'ir.values', 'get', 'meta', False, [(self.model,False)], True, rpc.session.context, True)
		id = self.screen.id_get()
		if id and len(actions):
			win = win_preference.win_preference(self.model, id, actions)
			win.run()
		elif id:
			self.updateStatus(_('No preference available for this resource !'))
		else:
			self.updateStatus(_('No resource selected !'))

	def modified_save(self):
		if self.screen.isModified():
			value = QMessageBox.question(self, _('Question'), _('This record has been modified\ndo you want to save it?'),QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
			if value == QMessageBox.Save:
				return self.sig_save()
			elif value == QMessageBox.Discard:
				self.sig_reload()
				return True
			else:
				return False
		return True

	def canClose(self, urgent=False):
		return self.modified_save()

	def actions(self):
		return self.screen.actions

	def sig_plugins(self):
		import plugins
		datas = {'model': self.model, 'ids':self.screen.ids_get(), 'id' : self.screen.id_get()}
		plugins.execute(datas)

