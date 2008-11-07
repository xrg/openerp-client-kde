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
#import base64 
import tempfile

from Koo.Common import Common
from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(ImageFormWidgetUi, ImageFormWidgetBase) = loadUiType( Common.uiPath('image.ui') ) 

class ImageFormWidget(AbstractFormWidget, ImageFormWidgetUi):

	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		ImageFormWidgetUi.__init__(self)
		self.setupUi(self)

		self.width = int( attrs.get( 'img_width', 300 ) )
		self.height = int( attrs.get( 'img_height', 100 ) )
		self.installPopupMenu( self.uiImage )
		self.connect( self.pushLoad, SIGNAL('clicked()'), self.loadImage )
		self.connect( self.pushSave, SIGNAL('clicked()'), self.saveImage )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.removeImage )
		self.pushSave.setEnabled( False )

	def setReadOnly(self, ro):
		self.pushLoad.setEnabled( not ro )
		self.pushRemove.setEnabled( not ro )

	def menuEntries(self):
		if self.model.value(self.name):
			enableApplication = True
		else:
			enableApplication = False

		if self.model.value(self.name):
			enableImage = True
		else:
			enableImage = False
		return [ (_('Open...'), self.openApplication, enableApplication),
			 ('&Show image...', self.showImage, enableImage) ]

	def openApplication(self):
		if not self.model.value(self.name):
			return
		fileName = tempfile.mktemp()
		fp = file(fileName,'wb')
		fp.write(self.model.value(self.name))
		fp.close()
		if os.name == 'nt':
			os.startfile(fileName)
		else:
			os.spawnlp(os.P_NOWAIT, 'kfmclient', 'kfmclient', 'exec', fileName )

	def showImage(self):
		if not self.model.value(self.name):
			return
		dialog = QDialog( self )
		label = QLabel( dialog )
		pix = QPixmap()
		pix.loadFromData( self.model.value(self.name) )
		label.setPixmap( pix )
		layout = QHBoxLayout( dialog )
		layout.addWidget( label )
		dialog.exec_()

	def removeImage(self):
		self.model.setValue(self.name, False)
		self.update()
		self.modified()

	def saveImage(self):
		name = QFileDialog.getSaveFileName( self, _('Save image as...') )
		if name.isNull():
			return
		try:
			fp = file(name, 'wb')
			fp.write(self.model.value(self.name))
			fp.close()
		except:
			QMessageBox.warning( self, _('Error saving file'), _('Could not save the image with the given file name. Please check that you have permissions.') )

	def loadImage(self):
		name = QFileDialog.getOpenFileName( self, _('Open image file...') )
		if not name.isNull():
			image = file(name).read()
			self.model.setValue(self.name, image )
			self.update()
			self.modified()

	def update(self):
		if self.model.value(self.name):
			img = QImage()
			img.loadFromData( self.model.value(self.name) )
			pix = QPixmap.fromImage( img.scaled( self.width, self.height, Qt.KeepAspectRatio, Qt.SmoothTransformation ) )
			self.uiImage.setPixmap( pix )
		else:
			self.clear()

	def clear(self):
		self.uiImage.setText( '(load an image)' )

	def showValue(self):
		if self.model.value(self.name):
			self.pushSave.setEnabled( True )
		else:
			self.pushSave.setEnabled( False )
		self.update()

	def store(self):
		pass

