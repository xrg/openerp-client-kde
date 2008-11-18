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
from Koo.Common import Options
from Koo import Rpc
from button import *

from FormView import FormView, FormContainer
from Koo.View.AbstractParser import *
from action import ActionFormWidget
from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class FormParser(AbstractParser):

	def create(self, parent, viewModel, node, fields, filter=None):
		self.viewModel = viewModel
		self.filter = filter
		self.widgetList = []
		# Create the view
		self.view = FormView( parent )
		# Parse and fill in the view
		container, on_write = self.parse( node, fields )
		container.expand()
		self.view.setWidget( container )
		return self.view, on_write

	def parse(self, root_node, fields, notebook=None, container=None):
		attrs = Common.nodeAttributes(root_node)
		on_write = attrs.get('on_write', '')

		if container == None :
			container = FormContainer(self.view, int(attrs.get('col',4)) )
		
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
			 	if 'string' in attrs:
 					caption = attrs.get( 'string', '' )
 				else:
 					caption = ""
				label = QLabel( container )
				label.setText( caption )
				container.addWidget( label, attrs )

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
				container.addWidget(label, attrs)

			elif node.localName=='newline':
				container.newRow()

			elif node.localName=='button':
				button = ButtonFormWidget(container, self.view, attrs )
				name = attrs['name']
				self.view.widgets[name] = button
				container.addWidget(button, attrs)

			elif node.localName=='notebook':
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
					} [Options.options['tabs_position']]
					
			        tab.setTabPosition( pos )

				attrs['colspan'] = attrs.get('colspan', 3)
				
				container.addWidget(tab, attrs)
				
				# We pass a container because othewise a new container would 
				# be created by parse() and we don't want that because the tab
				# itself doesn't have a container: it's each of it's pages
				# that will have a container.
				_ , on_write = self.parse(node, fields, tab, container)

			elif node.localName=='page':
				widget, on_write = self.parse(node, fields, notebook )
				widget.expand()
				notebook.addTab( widget, attrs.get('string','No String Attr.') )

			elif node.localName =='hpaned':
				widget = QSplitter( container )

				container.addWidget(widget, attrs)
				_, on_write = self.parse( node, fields, widget, container)

			elif node.localName =='vpaned':
				widget = QWidget( container )
				layout = QVBoxLayout( widget )
				layout.setContentsMargins( 0, 0, 0, 0 )
				container.addWidget(widget, attrs)
				_, on_write = self.parse( node, fields, layout, container)

			elif node.localName == 'child1':
				widget, on_write = self.parse( node, fields )
				notebook.addWidget( widget )

			elif node.localName == 'child2':
				widget, on_write = self.parse( node, fields )
 				notebook.addWidget( widget )

			elif node.localName =='action':
				name = str(attrs['name'])
				widget_act = ActionFormWidget( container, self.view, attrs)
				self.view.widgets[name] = widget_act
				container.addWidget(widget_act, attrs)

			elif node.localName=='field':
				name = attrs['name']
				del attrs['name']
				type = attrs.get('widget', fields[name]['type'])
				fields[name].update(attrs)
				fields[name]['model']=self.viewModel
				if not type in widgets_type:
					print "Data Type %s not implemented in the client" % (type)
					continue

				fields[name]['name'] = name
				# Create the appropiate widget for the given field type
				widget_act = widgets_type[type][0](container, self.view, fields[name])
				if self.filter:
					widget_act.node = node
					self.widgetList.append(widget_act)


				label = None
				if not int(attrs.get('nolabel', 0)):
					label = fields[name]['string']+' :'
					
				self.view.widgets[name] = widget_act
				attrs['colspan'] = int(attrs.get('colspan', widgets_type[ type ][1]))

				if not 'help' in attrs:
					attrs['help'] = fields[name].get('help', False)

				container.addWidget(widget_act, attrs, label)

			elif node.localName=='group':
				widget, on_write = self.parse( node, fields, notebook )
				# We don't expand the widget in 'group' as it should be 
				# automatically expanded when new rows are added to the grid.
				# See FormContainer.newRow()
 				container.addWidget( widget, attrs )

		return  container, on_write

				
import calendar
import float
import integer
import char
import checkbox
import reference
import binary
import textbox
import richtext
import many2many
import many2one
import selection
import one2many
import url
import image
import link
import web
import progressbar
#import audio
#import video

widgets_type = {
	'date': (calendar.DateFormWidget, 1),
	'time': (calendar.TimeFormWidget, 1),
	'datetime': (calendar.DateTimeFormWidget, 1),
	'float_time': (calendar.FloatTimeFormWidget, 1),
	'float': (float.FloatFormWidget, 1),
	'integer': (integer.IntegerFormWidget, 1),
	'selection': (selection.SelectionFormWidget, 1),
	'char': (char.CharFormWidget, 1),
	'boolean': (checkbox.CheckBoxFormWidget, 1),
	'reference': (reference.ReferenceFormWidget, 1),
	'binary': (binary.BinaryFormWidget, 1),
	'text': (textbox.TextBoxFormWidget, 1),
	'text_tag': (richtext.RichTextFormWidget, 1),
	'one2many': (one2many.OneToManyFormWidget, 1),
	'one2many_form': (one2many.OneToManyFormWidget, 1),
	'one2many_list': (one2many.OneToManyFormWidget, 1),
	'many2many': (many2many.ManyToManyFormWidget, 1),
	'many2one': (many2one.ManyToOneFormWidget, 1),
	'image' : (image.ImageFormWidget, 1),
	'url' : (url.UrlFormWidget, 1),
	'email' : (url.EMailFormWidget, 1),
	'callto' : (url.CallToFormWidget, 1),
	'sip' : (url.SipFormWidget, 1),
	'link' : (link.LinkFormWidget, 1),
	'web' : (web.WebFormWidget, 1),
	'progressbar' : (progressbar.ProgressBarFormWidget, 1),
	#'audio' : (audio.AudioFormWidget, 1, False),
	#'video' : (video.VideoFormWidget, 1, False)
}

# vim:noexpandtab: