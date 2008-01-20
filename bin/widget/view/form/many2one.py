##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: many2one.py 4773 2006-12-05 11:01:20Z ced $
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

import gettext

from common import common

import widget
from widget.screen import Screen

from modules.gui.window.win_search import win_search
import rpc

import service

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *


class dialog( QDialog ):
	def __init__(self, model, id=None, attrs={}):
		QWidget.__init__( self )
		loadUi( common.uiPath('dia_form_win_many2one.ui'), self )

		self.setMinimumWidth( 800 )
		self.setMinimumHeight( 600 )

		if ('string' in attrs) and attrs['string']:
			self.setWindowTitle( self.windowTitle() + ' - ' + attrs['string'])
			
		self.screen = Screen(model, parent = self)

		self.result = False
		if id:
			self.result = True
			self.screen.load([id])
		else:
			self.screen.new()

		self.model = None
		

		self.screen.display()
		self.layout().insertWidget( 0, self.screen  )
		self.connect( self.pushOk, SIGNAL("clicked()"), self.slotAccepted )
		self.connect( self.pushCancel, SIGNAL("clicked()"), self.slotCancel )

	def slotCancel( self ):
		self.result = False
		self.close()

	def closeEvent( self, *args ):
		self.slotCancel()

	def slotAccepted( self ):
		self.screen.current_view.store()

		if self.screen.current_model.validate():
			self.result = True
			self.screen.save_current()
			self.model = self.screen.current_model.name()
			self.close()
		else:
			self.result = False

class many2one(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('many2one.ui'), self )
		self.dia = None
		
		self.connect( self.pushNew, SIGNAL( "clicked()" ), self.slotNew )
		self.connect( self.pushOpen, SIGNAL( "clicked()" ), self.sig_activate )
		self.connect( self.pushClear, SIGNAL( "clicked()" ), self.clear )

 		self.model_type = attrs['relation']	
		# To build the menu entries we need to query the server so we only make 
		# the call if necessary and only once. Hence with self.menuLoaded we know
		# if we've got it in the 'cache'
 		self.menuLoaded = False
		self.newMenuEntries = []
 		self.newMenuEntries.append((_('Action'), lambda: self.click_and_action('client_action_multi'),0))
 		self.newMenuEntries.append((_('Report'), lambda: self.click_and_action('client_print_multi'),0))
 		self.newMenuEntries.append((None, None, None))

 		self.parent = parent
 		self.ok = True

		self.uiText.installEventFilter( self )
 		if attrs.get('completion',False):
 			ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', '', [], 'ilike', {})
 			if ids:
				self.load_completion(ids,attrs)

	def clear( self ):
		if self.model:
			self.model.setValue( self.name, False )
			self.uiText.clear()
			self.modified()

	def eventFilter( self, target, event):
		if self.model and event.type() == QEvent.KeyPress :
			if event.key()==Qt.Key_F1 or event.key()==Qt.Key_F2 or event.key() == Qt.Key_Tab:
				self.sig_key_press( target, event )
				return True
			else:
				self.sig_changed()
				return False
		return self.showPopupMenu( target, event )

	def load_completion(self,ids,attrs):
		## TODO:  Load Completion implemented. Need to find somewhere to test it.
		## Need to implement on_completion_match.
		##  liststore its the original gtk implemention. need to probe it.
		self.completion = QCompleter()
		self.completion.setCaseSensitivity( Qt.CaseInsensitive )
		self.uiText.setCompleter( self.completion )
		self.liststore = QStringListModel()
		liststore = []
		liststore2 = []
		for i,word in enumerate( ids ):
			if word[1][0] == '[':
				i = word[1].find( ']')
				s = word[1][1:i]
				s2 = word[1][i+2:]
				liststore2.append( [ ( str(s) + " " + str( s2 ), s2 )])
				liststore.append( s2 )
			else:
				liststore2.append( [ word[1],word[1] ])
				liststore.append( word[1])
		self.liststore.setStringList( liststore )
				
		self.completion.setModel( self.liststore )
		self.completion.setCompletionColumn( 0 )
	       
## 		self.completion.connect("match-selected", self.on_completion_match)

	def match_func(self, completion, key_string, iter, data):
		model = self.completion.get_model()
		modelstr = model[iter][0].lower()
		return modelstr.startswith(key_string)
		 
	def on_completion_match(self, completion, model, iter):
		current_text = self.uiText.get_text()
		current_text = model[iter][1]
		name = model[iter][1]
		domain = self.model.domain( self.name )
		context = self.model.context(  )
		ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', name, domain, 'ilike', context)
		if len(ids)==1:
			self.model.setValue( self.name, ids[0] )
			self.display()
			self.ok = True
		else:
			win = win_search(self.attrs['relation'], sel_multi=False, ids=map(lambda x: x[0], ids), context=context, domain=domain)
			ids = win.result
			if ids:
				name = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_get', [ids[0]], rpc.session.context)[0]
				self.model.setValue(self.name, name)

	def setReadOnly(self, value):
		self.uiText.setEnabled( not value )
		self.pushNew.setEnabled( not value )
		self.pushOpen.setEnabled( not value )
		self.pushClear.setEnabled( not value )

	def colorWidget(self):
		return self.uiText

	def sig_activate(self, *args):
		self.ok = False

		if self.model.value(self.name):
			if self.dia:
				del self.dia

			self.dia = dialog( self.attrs['relation'], self.model.get()[self.name], attrs=self.attrs)
			self.dia.exec_()
			if self.dia.result:
				self.slotDialogAccepted( self.dia.model )
		else:
			if not self.isReadOnly():
				domain = self.model.domain(self.name)
				context = self.model.context()

				ids = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_search', str(self.uiText.text()), domain, 'ilike', context)
				if len(ids)==1:
					self.model.setValue(self.name, ids[0])
					self.display()
					self.ok = True
					return True

				win = win_search(self.attrs['relation'], sel_multi=False, ids=map(lambda x: x[0], ids), context=context, domain=domain)
				win.exec_()
				ids = win.result
				if ids:
					name = rpc.session.execute('/object', 'execute', self.attrs['relation'], 'name_get', [ids[0]], rpc.session.context)[0]
					self.model.setValue(self.name, name)
		self.display()
		self.ok=True

	def slotNew(self):
		if self.dia:
			del self.dia
		self.dia = dialog(self.attrs['relation'], attrs=self.attrs)
		self.dia.exec_()
		self.slotDialogAccepted( self.dia.model )


	def sig_key_press(self, widget, event, *args):
		if event.key()==Qt.Key_F1:
			self.slotNew()
		elif event.key()==Qt.Key_F2 or event.key() == Qt.Key_Enter:
			self.sig_activate()
		elif event.key()==Qt.Key_Tab:
			return 
		return False


	def sig_changed(self, *args):
		if self.ok:
			if self.model.value(self.name):
				self.model.setValue(self.name, False)
				self.display()

	#
	# No update of the model, the model is updated in real time !
	#
	def store(self):
		pass

	def reset(self):
		self.ok = False
		self.uiText.clear()
		
	def showValue(self):
		self.ok=False
		res = self.model.value(self.name)
 		if res:
			self.uiText.setText( res )
			self.pushOpen.setIcon( QIcon( ":/images/images/folder.png"))
 		else:
			self.uiText.clear()
 			self.pushOpen.setIcon( QIcon( ":/images/images/find.png"))
		self.ok=True

	def menuEntries(self):
		value = self.model.value(self.name)
		if not self.menuLoaded:
			fields_id = rpc.session.execute('/object', 'execute', 'ir.model.fields', 'search',[('relation','=',self.model_type),('ttype','=','many2one'),('relate','=',True)])
			fields = rpc.session.execute('/object', 'execute', 'ir.model.fields', 'read', fields_id, ['name','model_id'], rpc.session.context)
			models_id = [x['model_id'][0] for x in fields if x['model_id']]
			fields = dict(map(lambda x: (x['model_id'][0], x['name']), fields))
			models = rpc.session.execute('/object', 'execute', 'ir.model', 'read', models_id, ['name','model'], rpc.session.context)
			for model in models:
				field = fields[model['id']]
				model_name = model['model']
#				print "field:", field, "model_name:",model_name
				f = lambda model_name,field: lambda: self.click_and_relate(model_name,field)					
				self.newMenuEntries.append(('... '+model['name'], f(model_name,field), False))
			self.menuLoaded = True
		# Set enabled/disabled values
		currentEntries = []
		for x in self.newMenuEntries:
			currentEntries.append( (x[0], x[1], value) )
		return currentEntries

	def slotDialogAccepted( self, value ):
		self.model.setValue(self.name, value)
		self.display()
		self.dia.close()
		if self.dia:
			del self.dia
			self.dia =None

	#
	# Open a view with ids: [(field,'=',value)]
	#
	def click_and_relate(self, model, field):
		value = self.model.value(self.name)
		ids = rpc.session.execute('/object', 'execute', model, 'search',[(field,'=',value)])
		obj = service.LocalService('gui.window')
		obj.create(False, model, ids, [(field,'=',value)], 'form', None, mode='tree,form')
		return True

	def click_and_action(self, type):
		id = self.model.value(self.name)
		obj = service.LocalService('action.main')
		res = obj.exec_keyword(type, {'model':self.model_type, 'id': id or False, 'ids':[id], 'report_type': 'pdf'})
		return True

