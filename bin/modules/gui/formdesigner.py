##############################################################################
#
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from common import common
import widget.view.form
import xml.dom.minidom

class FormDesigner(QMainWindow):
	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)
		loadUi( common.uiPath('designer.ui'), self )
		self.load()
		self.square = QWidget( self.uiContainer, Qt.Popup )
		self.square.setStyleSheet( 'background: black' )
		self.square.show()
		self.setMouseTracking( True )
		self.timer = QTimer( self )
		self.connect( self.timer, SIGNAL("timeout()"), self.highlight )
		self.timer.start( 100 )

	def load(self):
		x = """
			<form string="Attachments">
				<field colspan="4" name="name" select="1"/>
				<field colspan="4" name="datas" fname_widget="datas_fname" />
				<field name="datas_fname"/>
				<newline/>
				<field name="res_model" select="1" invisible="1" nolabel="1"/>
				<field name="res_id" invisible="1" nolabel="1"/>
				<separator colspan="4" string="Description"/>
				<field colspan="4" name="description" nolabel="1"/>
			</form>
			"""
		x = xml.dom.minidom.parseString( x )

		fields = { 
			'name': { 'name': 'name', 'type':'char', 'string': 'Name' },
			'datas' : { 'name': 'datas', 'type':'binary', 'string': 'Name' },
			'datas_fname' : {'name': 'datas_fname', 'type':'char', 'string': 'Name' },
			'res_model' : {'name': 'res_model', 'type': 'char', 'string': 'Name' },
			'res_id' : {'name': 'res_id', 'type': 'integer', 'string': 'Name' },
			'description' : {'name': 'description', 'type': 'text', 'string': 'Name' }
		}	
		for node in x.childNodes:
			if not node.nodeType == node.ELEMENT_NODE:
				continue
			print "SELF. ", self
			self.parser = widget.view.form.parser.FormParser()
			#parser.filter = self
			w = self.parser.create( self.uiContainer, 'ir.attachment', node, fields, toolbar = False, filter=self )
		
	def highlight(self):
		for x in self.parser.widgetList:
			if x.underMouse():

				pos = self.square.mapToParent( self.square.mapFromGlobal( x.mapToGlobal( x.mapFromParent(x.pos()) ) ) ) 
				pos -= QPoint(3, 3)
				self.square.move( pos )
				#self.square.move( x.mapToGlobal( x.mapFromParent(x.pos()) ) )
				size = x.size() + QSize( 6, 6 )
				self.square.resize( size )
				self.square.show()
				x.setStyleSheet( 'background: yellow' )
				print "TROBAT: ", x
				return
		
	def mouseMoveEvent(self, event):
		print "som dins"

	#def eventFilter(self, object, event):
		#print "HELLO: " + str(int(event.type()))
		#if ( event.type() == QEvent.MouseMove ):
			##self.square.setGeometry( object.geometry() )
			#print "moving?"
			#if object.geometry().contains( event.pos() ):
				#print "moving square"
				#self.square.move( self.square.mapFromGlobal( object.mapToGlobal( object.pos() ) ) )
				#self.square.size( object.size() )
			#return True
		#return False
