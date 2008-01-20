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
