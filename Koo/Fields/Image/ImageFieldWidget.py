##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import os
import base64 
import tempfile

from Koo.Common import Common
from Koo.Common import Icons
from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(ImageFieldWidgetUi, ImageFieldWidgetBase) = loadUiType( Common.uiPath('image.ui') ) 

class ImageFieldWidget(AbstractFieldWidget, ImageFieldWidgetUi):

	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		ImageFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self._isUpToDate = False
		self.width = int( attrs.get( 'img_width', 300 ) )
		self.height = int( attrs.get( 'img_height', 100 ) )
		self.installPopupMenu( self.uiImage )
		self.connect( self.pushLoad, SIGNAL('clicked()'), self.loadImage )
		self.connect( self.pushSave, SIGNAL('clicked()'), self.saveImage )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.removeImage )
		self.pushSave.setEnabled( False )

	def showEvent(self, event):
		if not self._isUpToDate:
			if self.getImage():
				self.pushSave.setEnabled( True )
			else:
				self.pushSave.setEnabled( False )
			self.update()
			self._isUpToDate = True
		return AbstractFieldWidget.showEvent(self, event)

	# This function is overriden in picture widget
	def getImage(self):
		return self.record.value(self.name)

	# This function is overriden in picture widget
	def setImage(self, value):
		self.record.setValue(self.name, value)

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		self.pushLoad.setEnabled( not value )
		self.pushRemove.setEnabled( not value )

	def menuEntries(self):
		if self.getImage():
			enableApplication = True
		else:
			enableApplication = False

		if self.getImage():
			enableImage = True
		else:
			enableImage = False
		return [ (_('Open...'), self.openApplication, enableApplication),
			 ('&Show image...', self.showImage, enableImage) ]

	def openApplication(self):
		if not self.getImage():
			return
		extension = ''
		# Under windows platforms we need to create the temporary
		# file with an appropiate extension, otherwise the system
		# won't be able to know how to open it. So we let Qt guess
		# what image format it is and use that as an extension.
		byte = QByteArray( str(self.getImage()) )
		buf = QBuffer( byte )
		buf.open( QBuffer.ReadOnly )
		reader = QImageReader( buf )
		if reader.canRead():
			extension = '.%s' % str( reader.format() )

		fileName = tempfile.mktemp( extension )
		fp = file(fileName,'wb')
		fp.write(self.getImage())
		fp.close()
		Common.openFile( fileName )

	def showImage(self):
		if not self.getImage():
			return
		dialog = QDialog( self )
		dialog.setWindowTitle( _('Image') )
		label = QLabel( dialog )
		pix = QPixmap()
		pix.loadFromData( self.getImage() )
		label.setPixmap( pix )
		layout = QHBoxLayout( dialog )
		layout.addWidget( label )
		dialog.exec_()

	def removeImage(self):
		self.setImage(False)
		self.update()
		self.modified()

	def saveImage(self):
		name = QFileDialog.getSaveFileName( self, _('Save image as...') )
		if name.isNull():
			return
		try:
			fp = file(unicode(name), 'wb')
			fp.write(self.getImage())
			fp.close()
		except:
			QMessageBox.warning( self, _('Error saving file'), _('Could not save the image with the given file name. Please check that you have permissions.') )
		Semantic.addInformationToFile( filename, self.record.group.resource, self.record.id, self.name )

	def loadImage(self):
		fileTypes = "*.png *.jpg *.jpeg *.gif *.tif *.xpm *.bmp"
		fileTypes = _('Image files (%s)') % fileTypes
		name = QFileDialog.getOpenFileName( self, _('Open image file...'), QDir.homePath(), fileTypes )
		if not name.isNull():
			image = file(unicode(name), 'rb').read()
			self.setImage( image )
			self.update()
			self.modified()

	def update(self):
		if self.getImage():
			img = QImage()
			img.loadFromData( self.getImage() )
			pix = QPixmap.fromImage( img.scaled( self.width, self.height, Qt.KeepAspectRatio, Qt.SmoothTransformation ) )
			self.uiImage.setPixmap( pix )
		else:
			self.clear()

	def clear(self):
		self.uiImage.setText( _('(no image)') )

	def showValue(self):
		if self.isVisible():
			if self.getImage():
				self.pushSave.setEnabled( True )
			else:
				self.pushSave.setEnabled( False )
			self.update()
			self._isUpToDate = True
		else:
			self._isUpToDate = False

	def store(self):
		pass

class ImageFieldDelegate( AbstractFieldDelegate ):
	def createEditor(self, parent, option, index):
		return None
	
	def sizeHint(self, option, index):
		return QSize(30, 30)

	def paint(self, painter, option, index):
		# Paint background if row/item is selected
		if (option.state & QStyle.State_Selected):
			painter.fillRect(option.rect, option.palette.highlight());

		value = index.model().recordFromIndex( index ).value( self.name )
		image = QImage()
		image.loadFromData( value )
		painter.drawImage( option.rect, image )

class PictureFieldWidget( ImageFieldWidget ):
	def __init__(self, parent, model, attrs={}):
		ImageFieldWidget.__init__(self, parent, model, attrs)
		self.pushLoad.hide()
		self.pushSave.hide()
		self.pushRemove.hide()

	def getImage(self):
		value = self.record.value(self.name)		

		if (isinstance(value, tuple) or isinstance(value,list)) and len(value)==2:
			type, data = value
		else:
			type, data = None, value

		if not data:
			return False

		if type == 'stock':
			stock, size = data
			return self.pixmapToData( Icons.kdePixmap( stock ) )
		else:
			return base64.decodestring(data)

	def pixmapToData(self, pixmap):
		if pixmap.isNull():
			return False
		bytes = QByteArray()
		buffer = QBuffer(bytes);
		buffer.open(QIODevice.WriteOnly);
		pixmap.save(buffer, "BMP")
		return str(bytes)

