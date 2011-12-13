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

from xml.parsers import expat

import sys
import gettext

from CustomSearchFormWidget import *
from SearchViewWidget import *
from SearchWidgetFactory import *
from AbstractSearchWidget import *
from Koo.Common import Common
from Koo.Common import Api
from Koo import Rpc

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Koo.Common.Ui import *

class SearchFormContainer( QWidget ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		layout = QGridLayout( self )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		# Maximum number of columns
		self.col = 4
		self.x = 0
		self.y = 0

	def addWidget(self, widget, name=None):
		if self.x + 1 > self.col:
			self.x = 0
			self.y = self.y + 1

		# Add gridLine attribute to all widgets so we can easily discover
		# in which line they are.
		widget.gridLine = self.y
		if name:
			label = QLabel( name )
			label.gridLine = self.y
			vbox = QVBoxLayout()
			vbox.setSpacing( 0 )
			vbox.setContentsMargins( 0, 0, 0, 0 )
			vbox.addWidget( label, 0 )
			vbox.addWidget( widget )
			self.layout().addLayout( vbox, self.y, self.x )
		else:
                	self.layout().addWidget( widget, self.y, self.x )
		self.x = self.x + 1

class SearchFormParser(object):
	def __init__(self, container, fields, model=''):
		self.fields = fields
		self.container = container
		self.model = model
		self.focusable = None
		self.widgets = {}

	def _psr_start(self, name, attrs):
		if name in ('form','tree','svg'):
			self.title = attrs.get('string','Form')
		elif name=='field':
			select = attrs.get('select', False) or self.fields[attrs['name']].get('select', False)
			if select:
				name = attrs['name']
				self.fields[name].update( attrs )
				self.fields[name]['model'] = self.model

				select = str(select)
				if select in self.widgets:
					self.widgets[ select ].append( name )
				else:
					self.widgets[ select ] = [ name ]

	def _psr_end(self, name):
		pass
	def _psr_char(self, char):
		pass
	def parse(self, xml_data):
		psr = expat.ParserCreate()
		psr.StartElementHandler = self._psr_start
		psr.EndElementHandler = self._psr_end
		psr.CharacterDataHandler = self._psr_char
		self.widgetDict={}
		psr.Parse(xml_data.encode('utf-8'))

		fieldNames = set()
		for line in sorted( self.widgets.keys() ):
			for name in self.widgets[ line ]:
				# Because field may have the select attribute twice (one for form and 
				# another one for tree) we only use the one with higher priority.
				if name in fieldNames:
					continue
				fieldNames.add( name )

				attributes = self.fields[name]
				type = attributes.get('widget', attributes['type'])
				widget = SearchWidgetFactory.create( type, name, self.container, attributes )
				if not widget:
					continue
				self.widgetDict[str(name)] = widget
				if 'string' in attributes:
					label = attributes['string']+' :'
				else:
					label = None
				self.container.addWidget( widget, label )
				if not self.focusable:
					self.focusable = widget
		return self.widgetDict

(SearchFormWidgetUi, SearchFormWidgetBase) = loadUiType( Common.uiPath('searchform.ui') )

## @brief This class provides a form with the fields to search given a model.
#
# This class will emit the 'search()' signal each time the user pushes the 'search' button.
# Then you can use the 'value()' function to obtain a domain-like list.
class SearchFormWidget(AbstractSearchWidget, SearchFormWidgetUi):
	## @brief Constructs a new SearchFormWidget.
	def __init__(self, parent=None):
		AbstractSearchWidget.__init__(self, '', parent)
		SearchFormWidgetUi.__init__(self)
		self.setupUi( self )
		
		self.model = None
		self.widgets = {}
		self.name = ''
		self.focusable = True
		self.expanded = True
		self._loaded = False
		self._storedFilters = {}

		self.pushExpander.setEnabled( False )
		self.pushClear.setEnabled( False )
		self.pushSearch.setEnabled( False )
		self.toggleView()

		# Fill in filters menu
		self.actionSave = QAction(self)
		self.actionSave.setText( _('&Save Current Filter') )
		self.actionSave.setIcon( QIcon( ':/images/save.png' ) )

		self.actionManage = QAction(self)
		self.actionManage.setText( _('&Manage Filters') )
		self.actionManage.setIcon( QIcon( ':/images/administration.png' ) )

		self.filtersMenu = QMenu( self )
		self.filtersMenu.addAction( self.actionSave )
		self.filtersMenu.addAction( self.actionManage )
		self.pushSave.setMenu( self.filtersMenu )
		self.pushSave.setDefaultAction( self.actionSave )

		# Hide Save button and filters which will be shown if needed in load() method
		self.pushSave.hide()
		self.uiStoredFilters.hide()

		self.connect( self.pushExpander, SIGNAL('clicked()'), self.toggleExpansion )
		self.connect( self.pushClear, SIGNAL('clicked()'), self.clear )
		self.connect( self.pushSearch, SIGNAL('clicked()'), self.search )
		self.connect( self.pushSwitchView, SIGNAL('clicked()'), self.toggleView )
		self.connect( self.actionSave, SIGNAL('triggered()'), self.save )
		self.connect( self.actionManage, SIGNAL('triggered()'), self.manage )
		self.connect( self.uiStoredFilters, SIGNAL('currentIndexChanged(int)'), self.setStoredFilter )

	def setStoredFilter(self, index):
		if index >= 0:
			id = self.uiStoredFilters.itemData( index ).toInt()[0]
			if id:
				storedDomain = eval( self._storedFilters[id]['domain'] )
			else:
				storedDomain = []
			self.uiCustomContainer.setValue( storedDomain )
		else:
			self.uiCustomContainer.setValue( [] )

	## @brief Returns True if it's been already loaded. That is: setup has been called.
	def isLoaded(self):
		return self._loaded

	## @brief Returns True if it has no widgets.
	def isEmpty(self):
		if len(self.widgets): return False
		else:
			return True

	# @brief Manage stored filters
	def manage(self):
		Api.instance.executeAction({
			'name': _('Manage Filters'),
			'res_model': 'ir.filters',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'domain': "[('model_id','=','%s'),('user_id','=',%s)]" % (self.model, Rpc.session.uid)
		}, data={}, context=Rpc.session.context)

	# @brief Store current search
	def save(self):
		name, ok = QInputDialog.getText(self, _('Save Filter'), _('What is the name of this filter?'))
		if not ok or not name:
			return
		Rpc.session.execute('/object', 'execute', 'ir.filters', 'create_or_replace', {
			'name': unicode(name), 
			'user_id': Rpc.session.uid,
			'model_id': self.model,
			'domain': str(self.value()),
			'context': str(Rpc.session.context),
		}, Rpc.session.context)
		self.load()

	def load(self):
		try:
			ids = Rpc.session.call('/object', 'execute', 'ir.filters', 'search', [
				('user_id','in',[Rpc.session.uid, False]),
				('model_id','=',self.model)
			], 0, False, False, Rpc.session.context)
		except Rpc.RpcException, e:
			# If server version is 5.0 and koo module is not installed ir.filters will not be
			# available
			return
			
		# Show filter-related widgets
		self.pushSave.show()
		self.uiStoredFilters.show()

		records = Rpc.session.execute('/object', 'execute', 'ir.filters', 'read', ids, [], Rpc.session.context)
		self.uiStoredFilters.clear()
		self.uiStoredFilters.addItem( '' )
		for record in records:
			self.uiStoredFilters.addItem( record['name'], record['id'] )
			self._storedFilters[ record['id'] ] = record

	## @brief Initializes the widget with the appropiate widgets to search.
	#
	# Needed fields include XML view (usually 'form'), fields dictionary with information
	# such as names and types, and the model parameter.
	def setup(self, xml, fields, model, domain):
		# We allow one setup call only
		if self._loaded:
			return 

		self._loaded = True
		self.pushExpander.setEnabled( True )
		self.pushClear.setEnabled( True )
		self.pushSearch.setEnabled( True )

		parser = SearchFormParser(self.uiSimpleContainer, fields, model)
		self.model = model

		self.widgets = parser.parse(xml)
		for widget in self.widgets.values():
			self.connect( widget, SIGNAL('keyDownPressed()'), self, SIGNAL('keyDownPressed()') )

		for x in domain:
			if len(x) >= 2 and x[0] in self.widgets and x[1] == '=':
				self.widgets[ x[0] ].setEnabled( False )

		# Don't show expander button unless there are widgets in the
		# second row
		self.pushExpander.hide()
		for x in self.widgets.values():
			if x.gridLine > 0:
				self.pushExpander.show()
				break

		self.name = parser.title
		self.focusable = parser.focusable
		self.expanded = True
		self.toggleExpansion()

		self.uiCustomContainer.setup( fields, domain )

		#self.uiSearchView.setup( xml, fields, model, domain )
		self.load()

	def keyPressEvent(self, event):
		if event.key() in ( Qt.Key_Return, Qt.Key_Enter ):
			self.search()

	def search(self):
		if self.isCustomSearch():
			# Do not emit the signal if the server raises an exception with the search
			# which unfortunately can happen in some cases such as some searches with properties.
			# (ie. [('property_product_pricelist.name','ilike','a')])
			value = self.value()
			proxy = Rpc.RpcProxy( self.model, useExecute=False )
			try:
				proxy.search( value, 0, False, False, Rpc.session.context )
			except Rpc.RpcException, e:
				number = 0
				for item in value:
					if not isinstance(item, tuple):
						continue

					valid = True
					try:
						self.uiCustomContainer.setItemValid
						proxy.search( [item], 0, False, False, Rpc.session.context )
					except Rpc.RpcException, e:
						valid = False

					self.uiCustomContainer.setItemValid(number, valid)
					number += 1

				QMessageBox.warning(self, _('Search Error'), _('Some items of custom search cannot be used. Please, change those in red and try again.'))
				return

			self.uiCustomContainer.setAllItemsValid(True)

		self.emit( SIGNAL('search()') )



	## @brief Shows Search and Clear buttons.
	def showButtons(self):
		self.pushClear.setVisible( True )
		self.pushSearch.setVisible( True )

	## @brief Hides Search and Clear buttons.
	def hideButtons(self):
		self.pushClear.setVisible( False )
		self.pushSearch.setVisible( False )

	def toggleExpansion(self):
		layout = self.uiSimpleContainer.layout()
		
		childs = self.uiSimpleContainer.children()
		for x in childs:
			if x.isWidgetType() and x.gridLine > 0:
				if self.expanded:
					x.hide()
				else:
					x.show()
		self.expanded = not self.expanded
		if self.expanded:
			self.pushExpander.setIcon( QIcon(':/images/up.png') )
		else:
			self.pushExpander.setIcon( QIcon(':/images/down.png') )

	def toggleView(self):
		if self.pushSwitchView.isChecked():
			self.uiSearchView.hide()
			self.uiSimpleContainer.hide()
			self.pushExpander.hide()
			self.uiCustomContainer.show()
		else:
			self.uiSearchView.hide()
			self.uiSimpleContainer.show()
			self.pushExpander.show()
			self.uiCustomContainer.hide()

	def setFocus(self):
		if self.focusable:
			self.focusable.setFocus()
		else:
			QWidget.setFocus(self)

	## @brief Clears all search fields.
	#
	# Calling 'value()' after this function should return an empty list.
	def clear(self):
		if self.pushSwitchView.isChecked():
			return self.uiCustomContainer.clear()

		for x in self.widgets.values():
			x.clear()

	## @brief Returns a domain-like list for the current search parameters.
	#
	# Note you can optionally give a 'domain' parameter which will be added to
	# the filters the widget will return.
	def value(self, domain=[]):
		index = self.uiStoredFilters.currentIndex()
		if index > 0:
			id = self.uiStoredFilters.itemData( index ).toInt()[0]
			storedDomain = eval( self._storedFilters[id]['domain'] )
			domain = domain + storedDomain

		if self.pushSwitchView.isChecked():
			return self.uiCustomContainer.value( domain )

		res = []
		for x in self.widgets:
			res += self.widgets[x].value()
		v_keys = [x[0] for x in res]
		for f in domain:
			if f[0] not in v_keys:
				res.append(f)
		return res

	def isCustomSearch(self):
		return self.pushSwitchView.isChecked()

	## @brief Allows setting filter values for all fields in the form.
	#
	# 'val' parameter should be a dictionary with field names as keys and
	# field values as values. Example:
	#
	# form.setValue({
	#	'name': 'enterprise',
	#	'income': 24
	# })
	def setValue(self, val):
		for x in val:
			if x in self.widgets:
				self.widgets[x].value = val[x]

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
