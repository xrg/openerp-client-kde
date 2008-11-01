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
from abstractformwidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ImageFormWidget(AbstractFormWidget):

	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		layout = QHBoxLayout( self )
		buttonsLayout = QVBoxLayout()
		self.uiImage = QLabel( self )
		self.uiImage.setAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
		self.uiImage.setText( _('(no image)') )
		self.pushLoad = QPushButton( self )
		self.pushSave = QPushButton( self )
		self.pushRemove = QPushButton( self )
		buttonsLayout.addWidget( self.pushLoad )
		buttonsLayout.addWidget( self.pushSave )
		buttonsLayout.addWidget( self.pushRemove )
		buttonsLayout.addStretch()
		layout.addWidget( self.uiImage )
		layout.addLayout( buttonsLayout )
		#self.pushLoad.setText( _('&Load image') )
		self.pushLoad.setIcon( QIcon( ':/images/images/open.png' ) )
		#self.pushSave.setText( _('&Save image') )
		self.pushSave.setIcon( QIcon( ':/images/images/save.png' ) )
		#self.pushRemove.setText( _('&Remove image') )
		self.pushRemove.setIcon( QIcon( ':/images/images/trash.png' ) )
		self.image = None

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

		if self.image:
			enableImage = True
		else:
			enableImage = False
		return [ (_('Open...'), self.openApplication, enableApplication),
			 ('&Show image...', self.showImage, enableImage) ]

	def openApplication(self):
		if not self.image:
			return
		fileName = tempfile.mktemp()
		fp = file(fileName,'wb')
		fp.write(self.image)
		fp.close()
		if os.name == 'nt':
			os.startfile(fileName)
		else:
			os.spawnlp(os.P_NOWAIT, 'kfmclient', 'kfmclient', 'exec', fileName )

	def showImage(self):
		if not self.image: 
			return
		dialog = QDialog( self )
		label = QLabel( dialog )
		pix = QPixmap()
		pix.loadFromData( self.image )
		label.setPixmap( pix )
		layout = QHBoxLayout( dialog )
		layout.addWidget( label )
		dialog.exec_()

	def removeImage(self):
		self.image = None
		self.update()
		self.modified()

	def saveImage(self):
		name = QFileDialog.getSaveFileName( self, _('Save image as...') )
		if name.isNull():
			return
		try:
			fp = file(name, 'wb')
			fp.write(self.image)
			fp.close()
		except:
			QMessageBox.warning( self, _('Error saving file'), _('Could not save the image with the given file name. Please check that you have permissions.') )

	def loadImage(self):
		name = QFileDialog.getOpenFileName( self, _('Open image file...') )
		if not name.isNull():
			self.image = file(name).read()
			self.update()
			self.modified()

	def update(self):
		if self.image:
			pix = QPixmap()
			pix.loadFromData(self.image)
			self.uiImage.setPixmap( pix.scaled( self.width, self.height, Qt.KeepAspectRatio ) )
		else:
			self.clear()

	def clear(self):
		self.uiImage.setText( '(load an image)' )
		self.image = None

	def showValue(self):
		self.image = self.model.value(self.name)
		if self.image:
			self.image = base64.decodestring(self.image)
			self.pushSave.setEnabled( True )
		else:
			self.pushSave.setEnabled( False )
		self.update()

	def store(self):
		if self.image:
			return self.model.setValue(self.name, base64.encodestring(self.image))
		else:
			return self.model.setValue(self.name, False)

