##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: reference.py 3061 2006-05-03 13:49:19Z pinky $
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

import form
from common import common
from many2one import dialog
from modules.gui.window.win_search import win_search

from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import rpc
from rpc import RPCProxy

class reference(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('reference.ui'), self )
		self.connect( self.pushNew, SIGNAL('clicked()'), self.new )
		self.connect( self.pushOpen, SIGNAL('clicked()'), self.open )
		self.connect( self.pushClear, SIGNAL('clicked()'), self.clear )
		self.setPopdown( attrs.get('selection',[]) )
		self.connect( self.uiModel, SIGNAL('currentIndexChanged(int)'), self.modelChanged )
		self.uiModel.setEditable( False )
		self.ok=True
		self._value=None

	def modelChanged(self, idx):
		if idx < 0:
			enabled = False
			self.uiText.clear()
		else:
			enabled = True
		self.uiText.setEnabled( enabled )
		self.pushOpen.setEnabled( enabled )
		self.pushNew.setEnabled( enabled )
		self.pushClear.setEnabled( enabled )

	def clear(self):
		# This automatically refreshes the widget and thus clears
		# the uiModel combo and the uiText line edit
		if self.model:
			self.model.setValue(self.name, False)

	def get_model(self):
                res = self.uiModel.currentText()
		return self._selection.get(res, False)

	def setPopdown(self, selection):
##		model = gtk.ListStore(gobject.TYPE_STRING)
		#model =[]
		#self._selection={}
		#self._selection2={}
		#lst = []
		self.invertedModels = {}

		for (i,j) in selection:
			self.uiModel.addItem( j, QVariant(i) )
			self.invertedModels[i] = j
			#name = str(j)
			#lst.append(name)
			#self._selection[name]=i
			#self._selection2[i]=name
		#for l in lst:
			#model.append( QString( l ) )
			#i = model.append()
			#model.set(i, 0, l)
			#self.widget_combo.child.set_text(l)
#		self.widget_combo.set_model(model)
#		self.widget_combo.set_text_column(0)
		#self.uiModel.addItems( model )
		#return lst

	def setReadOnly(self, value):
		self.uiModel.setEnabled( not value )
		if self.uiModel.currentIndex() < 0:
			value = True
		self.uiText.setEnabled( not value )
		self.pushNew.setEnabled( not value )
		self.pushOpen.setEnabled( not value )
		self.pushClear.setEnabled( not value )

	def colorWidget(self):
		return self.uiText

	def store(self):
		self.model.setValue(self.name, self._value)

	def sig_activate(self):
		#domain = self.modelField.domain_get()
		#context = self.modelField.context_get()
		domain = self.model.domain(self.name)
		context = self.model.fieldContext(self.name)
		#resource = self.get_model()
		resource = unicode(self.uiModel.itemData(self.uiModel.currentIndex()).toString())
		ids = rpc.session.execute('/object', 'execute', resource, 'name_search', unicode(self.uiText.text()), domain, 'ilike', context)
		
		if len(ids)==1:
			id, name = ids[0]
			#self.modelField.set_client((resource, (id, name)))
			self.model.setValue(self.name, (id, name) ) 
			self.display()
			self.ok = True
			return

		win = win_search(resource, sel_multi=False, ids=map(lambda x: x[0], ids), context=context, domain=domain)
		win.exec_()
		ids = win.result
		if ids:
			id, name = rpc.session.execute('/object', 'execute', resource, 'name_get', [ids[0]], rpc.session.context)[0]
			self.model.setValue(self.name, (resource, (id, name)) )
		self.display()

	def new(self):
		resource = unicode(self.uiModel.itemData(self.uiModel.currentIndex()).toString())
		dia = dialog(resource)
		#ok, value = dia.run()
		dia.exec_()
		#if ok:
			#self.modelField.set_client((self.get_model(), value))
		#	self.model.setValue(self.name, value)
		#	self.display()

	def open(self):
		if self._value:
			model, (id, name) = self._value
			dia = dialog(model, id)
			dia.exec_()
		else:
			self.sig_activate()

	def sig_changed_combo(self):
		self.uiText.setCurrentIndex(-1)
		self._value = False

	def sig_changed(self):
		if self.attrs.get('on_change',False) and self._value and self.ok:
			self.on_change(self.attrs['on_change'])
			AbstractFormWidget.sig_changed(self)
		elif self.ok:
			if self.model.value(self.name):
			#if self.modelField.get():
				self.model.setValue(self.name,False)
				#self.modelField.set_client(False)
				self.display()

	def clear(self):
		self.uiModel.setCurrentIndex(-1)
		
	def showValue(self):
		value = self.model.value(self.name) 
		self.ok = False
		if value:
			model, (id, name) = value
			self.uiModel.setCurrentIndex( self.uiModel.findText(self.invertedModels[model]) )
			self.sig_changed()
			if not name:
				id, name = RPCProxy(model).name_get([id], rpc.session.context)[0]
			self._value = model, (id, name)
			self.uiText.setText(name)
			self.setState('valid')
		else:
			self._value = False
			self.uiText.clear()
			self.setState('valid')
		self.ok = True

