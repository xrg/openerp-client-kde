##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: form.py 4698 2006-11-27 12:30:44Z ced $
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

from common import common
from common import icons
import service
import rpc

from form import ViewForm, FormContainer
from widget.view.abstractparser import *
from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class Button( QPushButton ):
	def __init__(self, attrs={}, parent = None , view = None) :
		QPushButton.__init__( self, parent )

		self.view = view
		self.attrs = attrs
		args = {
			'label': attrs.get('string', 'unknown')
		}

		if 'stylesheet' in attrs:
			self.setStyleSheet( attrs['stylesheet'] )

		#self.widget = self
		self.setText( args['label'] )
		if 'icon' in attrs:
			self.setIcon( icons.kdeIcon( attrs['icon'] ))
	
		self.connect( self ,SIGNAL('clicked()'), self.button_clicked)

	def button_clicked( self ): 
		model = self.view.screen.current_model
		self.view.store()
		if model.validate():
			id = self.view.screen.save_current()
			if not self.attrs.get('confirm',False) or \
					QMessageBox.question(self,_('Question'),self.attrs['confirm'],QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
				button_type = self.attrs.get('type', 'workflow')
				if button_type == 'workflow':
					rpc.session.execute('/object', 'exec_workflow', self.view.screen.name, self.attrs['name'], id)
				elif button_type == 'object':
					rpc.session.execute('/object', 'execute', self.view.screen.name, self.attrs['name'], [id], model.context())
				elif button_type == 'action':
					obj = service.LocalService('action.main')
					action_id = int(self.attrs['name'])
					obj.execute(action_id, {'model':self.view.screen.name, 'id': id,
									   'ids': [id]})
				else:
					raise 'Unallowed button type'
				self.view.screen.reload()
		else:
			#self.warn('misc-message', _('Invalid Form, correct red fields !'))
			notify.notifyWarning(_('Invalid Form, correct red fields!'))
			self.view.screen.display()

	def setReadOnly(self, value):
		self.setEnabled( not value )

	def setState(self, state):
		if self.attrs.get('states', False):
			my_states = self.attrs.get('states', '').split(',')
			if state not in my_states:
				self.hide()
			else:
				self.show()
		else:
			self.hide()


class FormParser(AbstractParser):

	def create(self, parent, viewModel, node, fields, toolbar, filter=None):
		self.viewModel = viewModel
		self.filter = filter
		self.widgetList = []
		# Create the view
		self.view = ViewForm( parent, toolbar )
		# Initialize the main container 
		attrs = common.node_attributes(node)
		if 'stylesheet' in attrs:
			self.view.setStyleSheet( attrs['stylesheet'] )
		self.view.widget.new(col=int(attrs.get('col', 4)))
		# Parse and fill in the view
		container, on_write = self.parse( node, fields, container=self.view.widget )
		return self.view, on_write

	def parse(self, root_node, fields, notebook=None, container=None):
		attrs = common.node_attributes(root_node)
		on_write = attrs.get('on_write', '')

		if container == None :
			container = FormContainer(self.view.widget)
			container.new(col=int(attrs.get('col', 4)))
		
		if not self.view.title:
			attrs = common.node_attributes(root_node)
			self.view.title = attrs.get('string', 'Unknown')

		for node in root_node.childNodes:
			if not node.nodeType==node.ELEMENT_NODE:
				continue
			attrs = common.node_attributes(node)
			if node.localName=='image':
				icon = QLabel(container)
				if 'stylesheet' in attrs:
					icon.setStyleSheet(attrs['stylesheet'])
				icon.setPixmap( icons.kdePixmap(attrs['name']) ) 
				container.addWidget(icon,colspan=int(attrs.get('colspan',1)),expand=int(attrs.get('expand',0)), ypadding=10, help=attrs.get('help', False) )

			elif node.localName=='separator':
			 	if 'string' in attrs:
 					label = attrs.get( 'string','No String Attr.' )
 				else:
 					label = ""
 				groupBox=QGroupBox( label, container )
				if 'stylesheet' in attrs:
					groupBox.setStyleSheet( attrs['stylesheet'] )
				container.new( groupBox )
				groupBox.setFlat( True )

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
				if 'stylesheet' in attrs:
					label.setStyleSheet( attrs['stylesheet'] )
				#label.set_use_markup(True)
				#if 'align' in attrs:
				#	try:
				#		label.set_alignment(float(attrs['align'] or 0.0), 0.5)
				#	except:
				#		pass
				#if 'angle' not in attrs:
				#	label.set_line_wrap(True)
				#label.set_angle(int(attrs.get('angle', 0)))
				container.addWidget(label, colspan=int(attrs.get('colspan', 1)), expand=False, help=attrs.get('help', False))

			elif node.localName=='newline':
				container.newline()

			elif node.localName=='button':
				button = Button(attrs, container, self.view )
				#button_list.append(button)
				self.view.buttons.append(button)
				container.addWidget(button, colspan=int(attrs.get('colspan', 1)), help=attrs.get('help', False))

			elif node.localName=='notebook':
				tab = QTabWidget( container )
				if 'stylesheet' in attrs:
					tab.setStyleSheet(attrs['stylesheet'])

				if attrs and 'tabpos' in attrs:
					pos = { 
						'up': QTabWidget.North,
						'down':QTabWidget.South,
						'left':QTabWidget.West,
						'right':QTabWidget.East
					} [attrs['tabpos']]
				else:
					pos = QTabWidget.West
					
			        tab.setTabPosition( pos )
				
				container.addWidget(tab, colspan=attrs.get('colspan', 3), expand=True )
				
				_ , on_write = self.parse(node, fields, tab)

			elif node.localName=='page':
				widget, on_write = self.parse(node, fields, notebook )
				widget.newline()

				notebook.addTab( widget, attrs.get('string','No String Attr.') )

			elif node.localName =='hpaned':
				widget = QSplitter( container )

				container.addWidget(widget, colspan=int(attrs.get('colspan', 4)), expand=True)
				_, on_write = self.parse( node, fields, widget, container)

			elif node.localName =='vpaned':
				widget = QWidget( container )
				layout = QVBoxLayout(  )
				layout.setMargin( 0 )
				widget.setLayout( layout )
				container.addWidget(widget, colspan=int(attrs.get('colspan', 4)), expand=True)
				_, on_write = self.parse( node, fields, layout, container)

			elif node.localName == 'child1':
				widget, on_write = self.parse( node, fields, None, None )
				notebook.addWidget( widget  )

			elif node.localName == 'child2':
				widget, on_write = self.parse( node, fields, None,None)
 				notebook.addWidget( widget )

			elif node.localName =='action':
				from action import action
				name = str(attrs['name'])
				widget_act = action(  container , None, attrs)
				self.view.widgets[name] = widget_act

				container.addWidget(widget_act, colspan=int(attrs.get('colspan', 3)), expand=True)

																  
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
				size = int(attrs.get('colspan', widgets_type[ type ][1]))
				expand = widgets_type[ type ][2]
				hlp = fields[name].get('help', attrs.get('help', False))

				container.addWidget(widget_act, label, expand, translate=fields[name].get('translate',False), colspan=size, fname=name, help=hlp)

			elif node.localName=='group':
				_ , on_write = self.parse(node, fields, notebook, container )

		#for (ebox,src,name,widget) in container.trans_box:
			#ebox.connect('button_press_event',self.translate, model, name, src, widget)




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


widgets_type = {
	'date': (calendar.DateFormWidget, 1, False),
	'time': (calendar.TimeFormWidget, 1, False),
	'datetime': (calendar.DateTimeFormWidget, 1, False),
	'float_time': (calendar.FloatTimeFormWidget, 1, False),
	'float': (float.FloatFormWidget, 1, False),
	'integer': (integer.IntegerFormWidget, 1, False),
	'selection': (selection.SelectionFormWidget, 1, False),
	'char': (char.CharFormWidget, 1, False),
	'boolean': (checkbox.CheckBoxFormWidget, 1, False),
	'reference': (reference.reference, 1, False),
	'binary': (binary.BinaryFormWidget, 1, False),
	'text': (textbox.TextBoxFormWidget, 1, True),
	'text_tag': (richtext.RichTextFormWidget, 1, True),
	'one2many': (one2many.OneToManyFormWidget, 1, True),
	'one2many_form': (one2many.OneToManyFormWidget, 1, True),
	'one2many_list': (one2many.OneToManyFormWidget, 1, True),
	'many2many': (many2many.many2many, 1, True),
	'many2one': (many2one.many2one, 1, False),
	'image' : (image.ImageFormWidget, 1, False),
	'url' : (url.UrlFormWidget, 1, False),
	'email' : (url.EMailFormWidget, 1, False),
	'callto' : (url.CallToFormWidget, 1, False),
	'sip' : (url.SipFormWidget, 1, False),
}

# vim:noexpandtab:
