from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *
from ocr import *

from template import *
from opentemplatedialog import *

from modules.gui.login import LoginDialog
import rpc

class ToolWidget(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		loadUi( 'toolwidget.ui', self )

		for x in TemplateBox.types:
			self.uiType.addItem( x )

		for x in TemplateBox.filters:
			self.uiFilter.addItem( x )

		self._box = None
		self.load()

	def setBox(self, box):
		self._box = box
		self.load()
		#self.tool.setTemplateBox( box )
	def getBox(self):
		return self._box
	box=property(getBox,setBox)

	def store(self):
		if not self._box:
			return
		self._box.rect = QRectF( self.uiX.value(), self.uiY.value(), self.uiWidth.value(), self.uiHeight.value() )
		self._box.type = unicode( self.uiType.currentText() )
		self._box.filter = unicode( self.uiFilter.currentText() )
		self._box.name = unicode( self.uiName.text() )
		self._box.text = unicode( self.uiText.text() )

	def enable(self, value):
		if not value:
			self.uiX.setValue( -1 )
			self.uiY.setValue( -1 )
			self.uiWidth.setValue( -1 )
			self.uiHeight.setValue( -1 )
		self.uiName.setEnabled( value )
		self.uiText.setEnabled( value )
		self.uiType.setEnabled( value )
		self.uiFilter.setEnabled( value )

	def load(self):
		if self._box:
			self.enable( True )
			self.uiX.setValue( self._box.rect.x() )
			self.uiY.setValue( self._box.rect.y() )
			self.uiWidth.setValue( self._box.rect.width() )
			self.uiHeight.setValue( self._box.rect.height() )
			self.uiType.setCurrentIndex( self.uiType.findText( self._box.type ) )
			self.uiFilter.setCurrentIndex( self.uiFilter.findText( self._box.filter ) )
			self.uiText.setText( self._box.text )
			self.uiName.setText( self._box.name )
		else:
			self.enable( False )


class TemplateBoxItem(QGraphicsRectItem):
	def __init__(self, rect):
		QGraphicsRectItem.__init__(self, rect)
		self.templateBox = None

class DocumentScene(QGraphicsScene):

	CreationMode = 1
	SelectionMode = 2

	MovingState = 1
	CreationState = 2

	def __init__(self, parent=None):
		QGraphicsScene.__init__(self,parent)
		self._imageBoxesVisible = True
		self._templateBoxesVisible = True
		self._binarizedVisible = False
		self._mode = self.CreationMode
		self._selection = None
		self._activeItem = None
		self._imageBoxes = None
		self._templateBoxes = []
		self._activeItemPen = QPen( QBrush( QColor('green') ), 1 )
		self._activeItemBrush = QBrush( QColor( 0, 255, 0, 50 ) )
		self._boxItemPen = QPen( QBrush( QColor( 'red' ) ), 1 )
		self._boxItemBrush = QBrush( QColor( 255, 0, 0, 50 ) )
		self._selectionPen = QPen( QBrush( QColor( 'blue' ) ), 1 )
		self._selectionBrush = QBrush( QColor( 0, 0, 255, 50 ) )
		self.state = None
		self.ocr = None
		self._image = None
		self._oneBitImage = None
		self._template = None

	def setDocument(self, fileName):
		self.clearImage()

		self.ocr = Ocr()
		self.ocr.scan( fileName )

		self._image = self.addPixmap( QPixmap( fileName ) )
		self._imageBoxes = self.createItemGroup( [] )
		for i in self.ocr.boxes:
			rect = QGraphicsRectItem( i.box )
			rect.setPen( self._boxItemPen )
			rect.setBrush( self._boxItemBrush )
			self._imageBoxes.addToGroup( rect )
		self.setImageBoxesVisible( self._imageBoxesVisible )
		self._imageBoxes.setZValue( 2 )

		self._oneBitImage = self.addPixmap( QPixmap( self.ocr.file ) )
		self._oneBitImage.setZValue( 1 )
		self.setBinarizedVisible( self._binarizedVisible )

		self.setTemplateBoxesVisible( self._templateBoxesVisible )

	def setTemplate(self, template):
		self.clearTemplate()
		self._template = template
		for x in self._template.boxes:
			item = self.addTemplateBox( x.rect )
			item.templateBox = x

	def isEnabled(self):
		if self._template and self.ocr:
			return True
		else:
			return False

	def clear(self):
		if self._imageBoxes:
			self.destroyItemGroup( self._imageBoxes )
		for x in self.items():
			self.removeItem( x )

	def clearTemplate(self):
		for x in self._templateBoxes:
			self.removeItem( x )

	def clearImage(self):
		if self._imageBoxes:
			self.destroyItemGroup( self._imageBoxes )
		if self._image:
			self.removeItem( self._image )
		if self._oneBitImage:
			self.removeItem( self._oneBitImage )

	def setImageBoxesVisible(self, value):
		self._imageBoxesVisible = value
		if self._imageBoxes:
			self._imageBoxes.setVisible( value )
		
	def setTemplateBoxesVisible(self, value):
		self._templateBoxesVisible = value
		for item in self.items():
			if item and unicode(item.data( 0 ).toString()) == 'TemplateBox':
				item.setVisible( value )

	def setBinarizedVisible(self, value):
		self._binarizedVisible = value
		self._oneBitImage.setVisible( value )

	def setMode(self, mode):
		self._mode = mode

	def setActiveItem(self, item):
		if self._activeItem:
			self._activeItem.setPen( self._selectionPen )
			self._activeItem.setBrush( self._selectionBrush )
		self._activeItem = item
		self._activeItem.setPen( self._activeItemPen )
		self._activeItem.setBrush( self._activeItemBrush )
		
	def addTemplateBox(self, rect):
		item = TemplateBoxItem( rect )
		item.setPen( self._selectionPen )
		item.setBrush( self._selectionBrush )
		item.setZValue( 5 )
		item.setData( 0, QVariant( 'TemplateBox' ) )
		self._templateBoxes.append( item )
		self.addItem( item )
		return item

	def mousePressEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode:
			item = self.itemAt( event.scenePos() )
			if item and unicode(item.data( 0 ).toString()) == 'TemplateBox':
				self.emit( SIGNAL('templateBoxSelected(PyQt_PyObject)'), item.templateBox )
				self.setActiveItem( item )
				return

			rect = QRectF(event.scenePos().x(), event.scenePos().y(), 1, 1)
			self._selection = self.addTemplateBox( rect )
		elif self._mode == self.SelectionMode:
			item = self.itemAt( event.scenePos() )
			if item != self._activeItem:
				self._activeItem.setBrush( QBrush() )
				self._activeItem.setPen( QPen() )
				self._activeItem = item
				self._activeItem.setBrush( self._activeItemBrush )
				self._activeItem.setBrush( self._activeItemBrush )

	def mouseReleaseEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode and self._selection:
			self._selection.setVisible( self._templateBoxesVisible )
			self.setActiveItem( self._selection )
			self._selection = None
			box = TemplateBox()
			box.rect = self._activeItem.rect()
			box.text = self.ocr.textInRegion( self._activeItem.rect() )
			self._template.addBox( box )
			self._activeItem.templateBox = box
			self.emit( SIGNAL('newTemplateBox(PyQt_PyObject)'), box )

	def mouseMoveEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode and self._selection:
			rect = self._selection.rect()
			rect.setBottomRight( event.scenePos() )
			self._selection.setRect( rect )
		
class MainWindow(QMainWindow):
	Unnamed = _('unnamed')

	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)
		loadUi( 'mainwindow.ui', self )
		self.scene = DocumentScene()
		self.uiView.setScene( self.scene )

		self._template = Template( self.Unnamed )
		self.scene.setTemplate(self._template)

		self.connect( self.scene, SIGNAL('newTemplateBox(PyQt_PyObject)'), self.setCurrentTemplateBox )
		self.connect( self.scene, SIGNAL('templateBoxSelected(PyQt_PyObject)'), self.setCurrentTemplateBox )
		self.connect( self.actionExit, SIGNAL('triggered()'), self.close )
		self.connect( self.actionOpenImage, SIGNAL('triggered()'), self.openImage )
		self.connect( self.actionOpenTemplate, SIGNAL('triggered()'), self.openTemplate )
		self.connect( self.actionToggleImageBoxes, SIGNAL('triggered()'), self.toggleImageBoxes )
		self.connect( self.actionToggleTemplateBoxes, SIGNAL('triggered()'), self.toggleTemplateBoxes )
		self.connect( self.actionToggleBinarized, SIGNAL('triggered()'), self.toggleBinarized )
		self.connect( self.actionLogin, SIGNAL('triggered()'), self.login )
		self.connect( self.actionSaveTemplate, SIGNAL('triggered()'), self.saveTemplate )
		self.connect( self.actionSaveTemplateAs, SIGNAL('triggered()'), self.saveTemplateAs )
		self.connect( self.actionNewTemplate, SIGNAL('triggered()'), self.newTemplate )
		self.toggleImageBoxes()
		QTimer.singleShot( 1000, self.setup )
		self.updateTitle()

	def setup(self):
		initOcrSystem()	
		#self.scene.setDocument( 'c-0.tif' )

		self.uiTool = ToolWidget( self.uiToolDock )
		self.uiTool.show()
		self.uiToolDock.setWidget( self.uiTool )

		rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'g1' )


	def setCurrentTemplateBox(self, box):
		if self.uiTool.box:
			self.uiTool.store()
		self.uiTool.box = box

	def openImage(self):
		fileName = QFileDialog.getOpenFileName( self )	
		if fileName.isNull():
			return
		print unicode( fileName )
		self.scene.setDocument( unicode( fileName ) )

	def toggleImageBoxes(self):
		self.scene.setImageBoxesVisible( self.actionToggleImageBoxes.isChecked() )	

	def toggleTemplateBoxes(self):
		self.scene.setTemplateBoxesVisible( self.actionToggleTemplateBoxes.isChecked() )

	def toggleBinarized(self):
		self.scene.setBinarizedVisible( self.actionToggleBinarized.isChecked() )

	def login(self):
		dialog = LoginDialog( self )
		if dialog.exec_() == QDialog.Rejected:
			return
		rpc.session.login( dialog.url, dialog.databaseName )

	def newTemplate(self):
		answer = QMessageBox.question(self, _('New Template'), _('Do you want to save changes to the current template?'), QMessageBox.Save | QMessageBox.No | QMessageBox.Cancel )
		if answer == QMessageBox.Cancel:
			return
		elif answer == QMessageBox.Save:
			if not self.saveTemplate():
				return
		self._template = Template( self.Unnamed )	
		self.scene.setTemplate( self._template )
		self.updateTitle()

	def saveTemplate(self):
		self.uiTool.store()
		if not self._template.id:
			(name, ok) = QInputDialog.getText( self, _('Save template'), _('Template name:') )
			if not ok:
				return False
			self._template.name = unicode(name)
				

		if self._template.id:
			rpc.session.call( '/object', 'execute', 'nan.template', 'write', [self._template.id], {'name': self._template.name } )
			ids = rpc.session.call( '/object', 'execute', 'nan.template.box', 'search', [('template_id','=',self._template.id)] )
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'unlink', ids )
		else:
			self._template.id = rpc.session.call( '/object', 'execute', 'nan.template', 'create', {'name': self._template.name } )
		for x in self._template.boxes:
			values = { 'x': x.rect.x(), 'y': x.rect.y(), 
				'width': x.rect.width(), 'height': x.rect.height(), 'template_id': self._template.id, 
				'name': x.name, 'text': x.text, 'type': x.type, 'filter': x.filter }
			print values
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'create', values )
		self.updateTitle()
		return True

	def saveTemplateAs(self):
		id = self._template.id
		self._template.id = 0
		if not self.saveTemplate():
			self._template.id = id
		self.updateTitle()

	def openTemplate(self):
		dialog = OpenTemplateDialog(self)
		if dialog.exec_() == QDialog.Rejected:
			return
		model = dialog.group[dialog.id]
		self._template = Template( model.value('name') )
		self._template.id = model.id

		fields = rpc.session.execute('/object', 'execute', 'nan.template.box', 'fields_get')
		model.value('boxes').addFields( fields )
		for x in model.value('boxes'):
			box = TemplateBox()
			box.rect = QRectF( x.value('x'), x.value('y'), x.value('width'), x.value('height') )
			box.name = x.value('name')
			box.text = x.value('text')
			box.type = x.value('type')
			box.filter = x.value('filter')
			self._template.addBox( box )

		self.scene.setTemplate(self._template)
		self.updateTitle()

	def updateTitle(self):
		self.setWindowTitle( "NaNnar - [%s]" % self._template.name )

