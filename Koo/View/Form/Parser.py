##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.Common import Common
from Koo.Common import Icons
from Koo.Common.Settings import *
from Koo import Rpc

from FormView import FormView, FormContainer
from Koo.View.AbstractParser import *
from Koo.Fields.FieldWidgetFactory import *
from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class FormParser(AbstractParser):

	def create(self, viewId, parent, viewModel, node, fields, filter=None):
		self.viewModel = viewModel
		self.filter = filter
		self.widgetList = []
		self.context = parent.context
		# Create the view
		self.view = FormView( parent )
		self.view.id = viewId
		# Parse and fill in the view
		container, onWriteFunction = self.parse( node, fields )
		self.view.setWidget( container )
		self.view.setOnWriteFunction( onWriteFunction )
		return self.view

	def parse(self, root_node, fields, notebook=None, container=None):
		attrs = Common.nodeAttributes(root_node)
		onWriteFunction = attrs.get('on_write', '')

		if container == None :
			parent = self.view
			if notebook:
				parent = notebook
			# We want FormContainer parent to be the notebook for the case
			# when it's a QTabWidget. This way FormContainer can enable/disable
			# the tab when necessary.
			container = FormContainer( parent, int(attrs.get('col',4)) )
		
		if not self.view.title:
			self.view.title = attrs.get('string', 'Unknown')

		for node in root_node.childNodes:
			if not node.nodeType==node.ELEMENT_NODE:
				continue
			attrs = Common.nodeAttributes(node)
			if node.localName=='image':
				icon = QLabel(container)
				icon.setPixmap( Icons.kdePixmap(attrs['name']) ) 
				container.addWidget(icon, attrs)

			elif node.localName=='separator':
				caption = attrs.get( 'string', '' )

				separator = QWidget( container )
				separator.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
				label = QLabel( separator )
				label.setText( caption )
				font = label.font()
				font.setBold( True )
				label.setFont( font )
				line = QFrame( separator )
				line.setFrameShape( QFrame.HLine )
				line.setFrameShadow( QFrame.Plain )
				layout = QVBoxLayout( separator )
				layout.setAlignment( Qt.AlignTop )
				layout.setContentsMargins( 0, 0, 0, 0 )
				layout.setSpacing( 0 )
				layout.addWidget( label )
				layout.addWidget( line )

				self.view.addStateWidget( separator, attrs.get('attrs'), attrs.get('states') )
				container.addWidget( separator, attrs )

			elif node.localName=='label':
				text = attrs.get('string', '')
				if not text:
					for node in node.childNodes:
						if node.nodeType == node.TEXT_NODE:
							text += node.data
						else:
							text += node.toxml()
				label = QLabel( text, container )
				label.setWordWrap( True )
				label.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
				container.addWidget(label, attrs)

			elif node.localName=='newline':
				container.newRow()

			elif node.localName=='button':
				button = FieldWidgetFactory.create( 'button', container, self.view, attrs )
				if not self.isWidgetVisible( attrs ):
					continue
				name = attrs.get('name', 'unnamed')
				self.view.widgets[name] = button
				self.view.addStateWidget( button, attrs.get('attrs'), attrs.get('states') )
				container.addWidget(button, attrs)

			elif node.localName=='notebook':
				if not self.isWidgetVisible( attrs ):
					continue
				tab = QTabWidget( container )
				if attrs and 'tabpos' in attrs:
					pos = { 
						'up': QTabWidget.North,
						'down':QTabWidget.South,
						'left':QTabWidget.West,
						'right':QTabWidget.East
					} [attrs['tabpos']]
				else:
					pos = {
						'left': QTabWidget.West,
						'top': QTabWidget.North,
						'right': QTabWidget.East,
						'bottom': QTabWidget.South
					} [Settings.value('koo.tabs_position')]
					
			        tab.setTabPosition( pos )

				attrs['colspan'] = attrs.get('colspan', 3)
				
				container.addWidget(tab, attrs)
				
				# We pass a container because othewise a new container would 
				# be created by parse() and we don't want that because the tab
				# itself doesn't have a container: it's each of it's pages
				# that will have a container.
				_ , onWriteFunction = self.parse(node, fields, tab, container)

			elif node.localName=='page':
				if not self.isWidgetVisible( attrs ):
					continue
				widget, onWriteFunction = self.parse(node, fields, notebook )
				# Mark the container as the main widget in a Tab. This way
				# we can enable/disable the whole tab easily.
				widget.isTab = True
				self.view.addStateWidget( widget, attrs.get('attrs'), attrs.get('states') )

				notebook.addTab( widget, Common.normalizeLabel( attrs.get('string', '') ) )

			elif node.localName =='hpaned':
				widget = QSplitter( Qt.Horizontal, container )

				container.addWidget(widget, attrs)
				self.parse( node, fields, widget, container)

			elif node.localName =='vpaned':
				widget = QSplitter( Qt.Vertical, container )

				container.addWidget(widget, attrs)
				self.parse( node, fields, widget, container)

			elif node.localName == 'child1':
				widget, onWriteFunction = self.parse( node, fields )
				notebook.addWidget( widget )

			elif node.localName == 'child2':
				widget, onWriteFunction = self.parse( node, fields )
 				notebook.addWidget( widget )

			elif node.localName =='action':
				name = str(attrs['name'])
				widget = FieldWidgetFactory.create( 'action', container, self.view, attrs )
				attrs['colspan'] = attrs.get('colspan', 3)
				self.view.widgets[name] = widget 
				container.addWidget(widget, attrs)

			elif node.localName=='field':
				if not self.isWidgetVisible( attrs ):
					continue
				name = attrs['name']
				del attrs['name']
				type = attrs.get('widget', fields[name]['type'])
				fields[name].update(attrs)
				fields[name]['model'] = self.viewModel

				# Create the appropiate widget for the given field type
				widget = FieldWidgetFactory.create( type, container, self.view, fields[name] )
				if not widget:
					continue

				fields[name]['name'] = name
				if self.filter:
					widget.node = node
					self.widgetList.append(widget)


				label = None
				if not int(attrs.get('nolabel', 0)):
					label = fields[name]['string']+' :'
					
				self.view.widgets[name] = widget
				#attrs['colspan'] = int(attrs.get('colspan', widgets_type[ type ][1]))

				if not 'help' in attrs:
					attrs['help'] = fields[name].get('help', False)

				container.addWidget(widget, attrs, label)

			elif node.localName=='group':
				if not self.isWidgetVisible( attrs ):
					continue
				widget, onWriteFunction = self.parse( node, fields, notebook )
				if 'string' in attrs:
					group = QGroupBox( notebook )
					group.setTitle( attrs['string'] )
					layout = QHBoxLayout( group )
					layout.setAlignment( Qt.AlignTop )
					layout.setContentsMargins( 0, 0, 0, 0 )
					layout.setSpacing( 0 )
					layout.addWidget( widget )
					widget = group
				
				self.view.addStateWidget( widget, attrs.get('attrs'), attrs.get('states') )
 				container.addWidget( widget, attrs )

		return  container, onWriteFunction

	def isWidgetVisible(self, attributes):
		value = attributes.get('invisible')
		if not value:
			return True
		return not eval(value, {'context':self.context})

# vim:noexpandtab:
