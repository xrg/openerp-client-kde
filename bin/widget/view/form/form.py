 ##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import rpc
import service

from widget.view.abstractview import *
from  abstractformwidget import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FormContainer( QWidget ):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.line = 0
		self.column = 0
		self.layout = QVBoxLayout( self )
		self.layout.setMargin( 0 )
		self.layout.setSpacing( 10  )
		self.layout.addStretch( 10 )
		self.widgets = []
		self.col = 0

	def new(self, widget=None, col=4):
		cp = self.currentParent()
		if cp:
			l = cp.layout()
			if l.rowCount() == 0:
				cp.hide()
				
		self.col = col
		if not widget:
			widget = QWidget( self )
		layout = QGridLayout( widget )
		layout.setMargin( 5 )
		self.layout.insertWidget( self.layout.count()-1, widget , -1)
		self.widgets.append( widget )
		self.line=0
		self.column=0

	def currentParent( self ):
		if len( self.widgets ) == 0:
			return None
		else:
			return self.widgets[ len( self.widgets ) -1 ]

	def addWidget(self, widget, name=None, expand=False, ypadding=2, rowspan=1, colspan=1, translate=False, fname=None, help=False):

		if colspan >= self.col -1 :
			colspan = self.col 
			
		a = name and 1 or 0
		if colspan + self.column + a  > self.col  :
			self.newline()
		
		current_wgt = self.currentParent()
		current_layout = current_wgt.layout()

		if name:
			#TODO: Test tooltip implementation
			label  = QLabel( name, self )
			label.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
			if help:
				label.setToolTip( help )
			current_layout.addWidget( label,self.line,self.column )
			self.column = self.column + 1

		current_layout.addWidget( widget,self.line,self.column, rowspan, colspan )
		self.column = self.column + colspan

	def newline(self):
		self.line = self.line + 1
		self.column = 0

class ViewForm( AbstractView ):
	def __init__(self, screen, toolbar):
		AbstractView.__init__( self, screen )
		self.view_type = 'form'
		self.screen = screen
		self.model_add_new = False
		self.title = ""
		self.model = None

		layout = QHBoxLayout( self )
		layout.setObjectName( 'HorizontalLayout' )

		self.widget = FormContainer( self )
		layout.setMargin( 0 )
		layout.addWidget( self.widget, 10  )


		# The parser will append all the buttons here
		self.buttons = []		
		# The parser will include all the widgets here with {name: widget} structure
		self.widgets = {}
		
		# Show the toolbar on the right
		if toolbar:
			toolWgt = QToolBar(self)
			toolWgt.setOrientation( Qt.Vertical )
			toolWgt.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
			separator = False
			self.actions = dict()
			for icontype in ( 'print','action','relate' ):
				for tool in toolbar[icontype]:
					separator = True
					action = toolWgt.addAction( QIcon( ":/images/images/"+icontype+".png"), tool['string'] )
					self.actions[ action ] = tool
					if icontype == 'relate':
						QObject.connect( action, SIGNAL("triggered()"),self._relate )
					elif icontype in ( 'action','print' ):
						QObject.connect( action, SIGNAL("triggered()"),self._action )
				if separator:
					toolWgt.addSeparator()
					separator=False

			layout.addWidget( toolWgt )

	def _relate( self ):
		action = self.sender( )
		tool = self.actions[ action ]				     
		print tool
	        #data = ( tool['model_id'][1], tool['name'] )
		data = ( tool['id'], tool['name'] )
		id = self.model and self.model.id
		if not (id):
			QMessageBox.information( self, '', _('You must select a record to use the relate button !'))
		model,field = data
		ids = rpc.session.execute('/object', 'execute', model, 'search',[(field,'=',id)])
		obj = service.LocalService('gui.window')
		return obj.create(False, model, ids, [(field,'=',id)], 'form', None, mode='tree,form')
		
	def _action( self ):
		action = self.sender()
		action = self.actions[ action ]
		self.screen.save_current()
		id = self.model and self.model.id
		if not (id):
			QMessageBox.information(self, '', _('You must save this record to use the relate button !'))
			return False
		data = {
			'id': id,
			'ids': [id]
		}
		self.screen.display()
		obj = service.LocalService('action.main')
		value = obj._exec_action(action, data)
		self.screen.reload()
		return value
		
	def __getitem__(self, name):
		return self.widgets[name]
	
	def store(self):
		if not self.model:
			return
		
		for name in self.widgets:
			if self.widgets[name].model:
				self.widgets[name].store()
			else:
				# TODO: Why does this happen?
				print "NO MODEL SET FOR WIDGET: ", name

	def selectedIds(self):
		if self.model:
			return [self.model.id]
		return []

	def reset(self):
		for wid_name, widget in self.widgets.items():
			widget.reset()

	def display(self, currentModel, models):
		self.model = currentModel

		if self.model and ('state' in self.model.mgroup.fields):
			#state = self.model['state'].get(self.model)
			state = self.model.value('state')
		else:
			state = 'draft'
		for name in self.widgets:
			from action import action
 			if isinstance(self.widgets[name], action):
 	                        #self.widgets[name].display(model, False)
				self.widgets[name].load( self.model, False )
 			else:
				if self.model:
					#self.widgets[name].display( model[name], state)
					self.widgets[name].load(self.model, state)
				else:
					#self.widgets[name].display( None, state)
					self.widgets[name].load(None, state)
				
		for button in self.buttons: 
			button.setState(state)

