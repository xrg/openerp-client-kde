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

from xml.parsers import expat

import sys
import gettext

from abstractsearchwidget import *
from common import common

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *

class SearchFormContainer( QWidget ):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		layout = QGridLayout( self )
		layout.setSpacing( 20 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		self.col = 8
		self.cont = [ (0, 0) ]

	def addNewLine(self):
		(x, y) = self.cont[-1]
		if x>0:
			self.cont[-1] = ( 0, y+1 )
		else:
			self.cont[-1] = ( x+1, self.col )

	def addWidget(self, widget, l=1, name=None, expand=False, ypadding=0):
		(x, y) = self.cont[-1]
		if l>self.col:
			l=self.col
		if l+x>self.col:
			self.addNewLine()
			(x, y) = self.cont[-1]

		widget.gridLine = y
		if name:
			label = QLabel( name )
			label.gridLine = y
			vbox = QVBoxLayout()
			vbox.setSpacing( 0 )
			vbox.setContentsMargins( 0, 0, 0, 0 )
			vbox.addWidget( label, 0 )
			vbox.addWidget( widget )
			self.layout().addLayout( vbox, y, x )
		else:
                	self.layout().addWidget( widget, y, x  )
          	self.cont[-1] = (x+l, y)

class SearchFormParser(object):
	def __init__(self, container, fields, model=''):
		self.fields = fields
		self.container = container
		self.model = model
		self.focusable = None
		
	def _psr_start(self, name, attrs):
		if name in ('form','tree'):
			self.title = attrs.get('string','Form')
		elif name=='field':
			if attrs.get('select', False) or self.fields[attrs['name']].get('select', False):
				type = attrs.get('widget', self.fields[attrs['name']]['type'])
				self.fields[attrs['name']].update(attrs)
				self.fields[attrs['name']]['model']=self.model
				widget_act = widgets_type[ type ][0](attrs['name'], self.container, self.fields[attrs['name']])
				if 'string' in self.fields[attrs['name']]:
					label = self.fields[attrs['name']]['string']+' :'
				else:
					label = None
				self.dict_widget[str(attrs['name'])] = widget_act
				size = widgets_type[ type ][1]
				if not self.focusable:
					self.focusable = widget_act
				self.container.addWidget(widget_act, size, label, int(self.fields[attrs['name']].get('expand',0)))

	def _psr_end(self, name):
		pass
	def _psr_char(self, char):
		pass
	def parse(self, xml_data):
		psr = expat.ParserCreate()
		psr.StartElementHandler = self._psr_start
		psr.EndElementHandler = self._psr_end
		psr.CharacterDataHandler = self._psr_char
		self.dict_widget={}
		psr.Parse(xml_data.encode('utf-8'))
		return self.dict_widget

## @brief This class provides a form with the fields to search given a model.
class SearchFormWidget(AbstractSearchWidget):
	def __init__(self, parent=None):
		AbstractSearchWidget.__init__(self, '', parent)
		loadUi( common.uiPath('searchform.ui'), self)
		
		self.model = None
		self.widgets = {}
		self.name = ''
		self.focusable = True
		self.expanded = True

		self.connect( self.pushExpander, SIGNAL('clicked()'), self.toggleExpansion )
		self.connect( self.pushClear, SIGNAL('clicked()'), self.clear )
		self.connect( self.pushSearch, SIGNAL('clicked()'), self.search )

		self.pushExpander.setEnabled( False )
		self.pushClear.setEnabled( False )
		self.pushSearch.setEnabled( False )

	def setup(self, xml, fields, model):
		# We admit one setup call only
		if self.model:
			return

		self.pushExpander.setEnabled( True )
		self.pushClear.setEnabled( True )
		self.pushSearch.setEnabled( True )

		parser = SearchFormParser(self.uiContainer, fields, model)
		self.model = model

		self.widgets = parser.parse(xml)
		self.name = parser.title
		self.focusable = parser.focusable
		self.expanded = True
		self.toggleExpansion()

	def search(self):
		self.emit( SIGNAL('search()') )

	def showButtons(self):
		self.pushClear.setVisible( True )
		self.pushSearch.setVisible( True )

	def hideButtons(self):
		self.pushClear.setVisible( False )
		self.pushSearch.setVisible( False )

	def toggleExpansion(self):
		layout = self.uiContainer.layout()
		
		childs = self.uiContainer.children()
		for x in childs:
			if x.isWidgetType() and x.gridLine > 0:
				if self.expanded:
					x.hide()
				else:
					x.show()
		self.expanded = not self.expanded
		if self.expanded:
			self.pushExpander.setIcon( QIcon(':/images/images/up.png') )
		else:
			self.pushExpander.setIcon( QIcon(':/images/images/down.png') )
		
	def setFocus(self):
		if self.focusable:
			self.focusable.setFocus()
		else:
			QWidget.setFocus(self)

	def clear(self):
		for x in self.widgets.values():
			x.clear()

	def getValue(self, domain=[]):
		res = []
		for x in self.widgets:
			res+=self.widgets[x].value
		v_keys = [x[0] for x in res]
		for f in domain:
			if f[0] not in v_keys:
				res.append(f)
		return res

	def setValue(self, val):
		for x in val:
			if x in self.widgets:
				self.widgets[x].value = val[x]

import calendar
import floatsearchwidget
import integersearchwidget
import selection
import char
import checkbox
import reference

widgets_type = {
	'date': (calendar.DateSearchWidget, 3),
	'time': (calendar.TimeSearchWidget, 3),
	'datetime': (calendar.DateSearchWidget, 3),
	'float': (floatsearchwidget.FloatSearchWidget, 2),
	'integer': (integersearchwidget.IntegerSearchWidget, 2),
	'selection': (selection.selection, 2),
	'many2one_selection': (selection.selection, 2),
	'char': (char.char, 2),
	'boolean': (checkbox.checkbox, 2),
	'text': (char.char, 2),
	'email': (char.char, 2),
	'url': (char.char, 2),
	'many2one': (char.char, 2),
	'one2many': (char.char, 2),
	'one2many_form': (char.char, 2),
	'one2many_list': (char.char, 2),
	'many2many_edit': (char.char, 2),
	'many2many': (char.char, 2),
	'reference': (reference.ReferenceSearchWidget, 2)
}
