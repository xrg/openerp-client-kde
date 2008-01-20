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
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class _container( QWidget ):
	def __init__(self, max_width):
		QWidget.__init__( self, None )
		self.cont = []
		self.max_width = max_width	
		self.width = {}
		self.layout = QVBoxLayout(self)

	def new(self, col=2, widget=None):
		self.col = col
		if not widget:
			widget = QWidget(self)
		layout = QGridLayout( widget )
		layout.setSpacing( 1 )
		self.layout.addWidget( widget )
		self.cont.append(  ( widget, 0, 0 )  )

	def get(self):
		return self.cont[-1][0]

	def pop(self):
		(table, x, y) = self.cont.pop()
		return table

	def newline(self):
		(table, x, y) = self.cont[-1]
		if x>0:
			self.cont[-1] = (table, 0 ,y+1 )
		else:
			self.cont[-1] = ( table ,x+1, self.col )

	def wid_add(self, widget, l=1, name=None, expand=False, ypadding=0):
		(table, x, y) = self.cont[-1]
		if l>self.col:
			l=self.col
		if l+x>self.col:
			self.newline()
			(table, x, y) = self.cont[-1]

                currentLayout = table.layout()
		if name:
			vbox = QVBoxLayout()
			label = QLabel( name )
			vbox.addWidget( label )
			vbox.addWidget( widget )
			vbox.setSpacing( 0 )
			currentLayout.addLayout( vbox, y, x )
		else:
                	currentLayout.addWidget( widget, y, x  )
          	self.cont[-1] = (table, x+l, y)
		width = widget.width()
		height = widget.height()
		self.width[('%d.%d') % (x,y)] = width

class parse(object):
	def __init__(self, parent, fields, model=''):
		self.fields = fields
		self.parent = parent
		self.model = model
		self.col = 8
		self.focusable = None
		
	def _psr_start(self, name, attrs):
		if name in ('form','tree'):
			self.title = attrs.get('string','Form')
			self.container.new(self.col)
		elif name=='field':
			if attrs.get('select', False) or self.fields[attrs['name']].get('select', False):
				type = attrs.get('widget', self.fields[attrs['name']]['type'])
				self.fields[attrs['name']].update(attrs)
				self.fields[attrs['name']]['model']=self.model
				widget_act = widgets_type[ type ][0](attrs['name'], self.parent, self.fields[attrs['name']])
				if 'string' in self.fields[attrs['name']]:
					label = self.fields[attrs['name']]['string']+' :'
				else:
					label = None
				self.dict_widget[str(attrs['name'])] = widget_act
				size = widgets_type[ type ][1]
				if not self.focusable:
					self.focusable = widget_act
				self.container.wid_add(widget_act, size, label, int(self.fields[attrs['name']].get('expand',0)))

	def _psr_end(self, name):
		pass
	def _psr_char(self, char):
		pass
	def parse(self, xml_data, max_width):
		psr = expat.ParserCreate()
		psr.StartElementHandler = self._psr_start
		psr.EndElementHandler = self._psr_end
		psr.CharacterDataHandler = self._psr_char
		self.notebooks=[]
		self.container=_container(max_width)
		self.dict_widget={}
		psr.Parse(xml_data.encode('utf-8'))
		self.widget = self.container
		return self.dict_widget

class form(AbstractSearchWidget):
	def __init__(self, xml, fields, model=None, parent=None):
		AbstractSearchWidget.__init__(self, 'Form', parent)
		parser = parse(self, fields, model=model)
		self.model = model

		#get the size of the window and the limite / decalage Hbox element
		ww = self.parent().width()

		self.widgets = parser.parse(xml, ww)
		self.widget = parser.widget
		self.focusable = parser.focusable
		self.id=None
		self.name=parser.title
		self.value = ''

	def setFocus(self):
		if self.focusable:
			self.focusable.setFocus()
		else:
			QWidget.setFocus(self)

	def clear(self):
		self.id=None
		for x in self.widgets.values():
			x.clear()

	def getValue(self):
		res = []
		for x in self.widgets:
			res+=self.widgets[x].value
		return res

	def setValue(self, val):
		for x in val:
			if x in self.widgets:
				self.widgets[x].value = val[x]
	value = property(getValue, setValue, None,
	  'The content of the form or excpetion if not valid')

import calendar
import floatsearchwidget
import integersearchwidget
import selection
import char
import checkbox
#import reference

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
	#'reference': (reference.reference, 2),
	'text': (char.char, 2),
	'email': (char.char, 2),
	'url': (char.char, 2),
	'many2one': (char.char, 2),
	'one2many': (char.char, 2),
	'one2many_form': (char.char, 2),
	'one2many_list': (char.char, 2),
	'many2many_edit': (char.char, 2),
	'many2many': (char.char, 2),
}
