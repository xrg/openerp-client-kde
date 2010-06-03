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

import os
import tempfile

from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from Koo.Common import Common
from Koo.Common import Semantic
from Koo.Common import Numeric

try:
	from NanScan.ScanDialog import ScanDialog, AbstractImageSaverFactory, AbstractImageSaver
	isNanScanAvailable = True
except:
	isNanScanAvailable = False

if isNanScanAvailable:
	class BinaryImageSaverFactory(AbstractImageSaverFactory):
		def __init__(self, record, field):
			self.record = record
			self.field = field

		def create(self, parent):
			saver = BinaryImageSaver( parent )
			saver.record = self.record
			saver.field = self.field
			return saver

	class BinaryImageSaver(AbstractImageSaver):
		def run(self):
			self.error = True
			image = QBuffer()
			if self.item.image.save( image, 'PNG' ):
				self.error = False
				self.record.setValue( self.field, str( image.buffer() ) )

(BinaryFieldWidgetUi, BinaryFieldWidgetBase) = loadUiType( Common.uiPath('binary.ui') ) 

class BinaryFieldWidget(AbstractFieldWidget, BinaryFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		BinaryFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.filters = attrs.get('filters', '*')
		if isinstance( self.filters, basestring ):
			self.filters = self.filters.split(',')
		self.filters = _('Files (%s)') % ' '.join( self.filters )

		self.fileNameField = attrs.get('filename')
		self.baseDirectory = unicode( QDir.homePath() )

		self.connect( self.pushRemove, SIGNAL('clicked()'),self.remove )

		self.actionNew = QAction(self)
		self.actionNew.setText( _('&New') )
		self.actionNew.setIcon( QIcon( ':/images/new.png' ) )

		self.actionScan = QAction(self)
		self.actionScan.setText( _('&Scan') )
		self.actionScan.setIcon( QIcon( ':/images/scanner.png' ) )

		self.newMenu = QMenu( self )
		self.newMenu.addAction( self.actionNew )
		if isNanScanAvailable:
			self.newMenu.addAction( self.actionScan )
		self.pushNew.setMenu( self.newMenu )
		self.pushNew.setDefaultAction( self.actionNew )

		self.actionSave = QAction(self)
		self.actionSave.setText( _('&Save') )
		self.actionSave.setIcon( QIcon( ':/images/save.png' ) )
		self.actionOpen = QAction(self)
		self.actionOpen.setText( _('&Open') )
		self.actionOpen.setIcon( QIcon( ':/images/open.png' ) )
		self.actionShowImage = QAction(self)
		self.actionShowImage.setText( _('Show &image'), )
		self.actionShowImage.setIcon( QIcon( ':/images/convert.png' ) )

		self.saveMenu = QMenu( self )
		self.saveMenu.addAction( self.actionSave )
		self.saveMenu.addAction( self.actionOpen )
		self.saveMenu.addAction( self.actionShowImage )
		self.pushSave.setMenu( self.saveMenu )
		self.pushSave.setDefaultAction( self.actionSave )

		self.connect( self.actionNew, SIGNAL('triggered()'), self.new )
		self.connect( self.actionScan, SIGNAL('triggered()'), self.scan )
		self.connect( self.actionSave, SIGNAL('triggered()'), self.save )
		self.connect( self.actionOpen, SIGNAL('triggered()'), self.open )
		self.connect( self.actionShowImage, SIGNAL('triggered()'), self.showImage )
		self.connect( self.saveMenu, SIGNAL('aboutToShow()'), self.updateShowImageAction )

		self.uiBinary.setAcceptDrops( True )
		self.installPopupMenu( self.uiBinary )

		self.sizeName = '%s.size' % self.name 
		
	def eventFilter(self, target, event):
		if not event.type() in (QEvent.Drop, QEvent.DragEnter, QEvent.DragMove):
			return AbstractFieldWidget.eventFilter(self, target, event)
		if not event.mimeData().hasText():
			return AbstractFieldWidget.eventFilter(self, target, event)
		if event.type() in (QEvent.DragMove, QEvent.DragEnter):
			event.accept()
			return True
		path = unicode( event.mimeData().text() ).replace( 'file://', '' )
		self.setBinaryFile( path )
		return True

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		self.uiBinary.setEnabled( not value )
		self.pushNew.setEnabled( not value )
		self.pushRemove.setEnabled( not value )
		self.updateActions()

	def updateShowImageAction(self):
		pix = QPixmap()
		if self.record and pix.loadFromData( self.record.value(self.name) ):
			self.actionShowImage.setEnabled( True )
		else:
			self.actionShowImage.setEnabled( False )
		
	def updateActions(self):
		if self.record and self.record.value(self.sizeName):
			enable = True
		else:
			enable = False
		self.actionSave.setEnabled( enable )
		self.actionOpen.setEnabled( enable )
		self.actionShowImage.setEnabled( enable )

	def menuEntries(self):
		enableApplication = False
		enableImage = False
		if self.record.value(self.name):
			enableApplication = True
			pix = QPixmap()
			if pix.loadFromData( self.record.value(self.name) ):
				enableImage = True

		return [ (_('Open...'), self.open, enableApplication), 
			 (_('Show &image...'), self.showImage, enableImage) ]

	def scan(self):
		from NanScan.ScanDialog import ScanDialog
		
		saver = BinaryImageSaverFactory( self.record, self.name )

		dialog = ScanDialog( self )
		dialog.setImageSaverFactory( saver )
		dialog.show()

	def open(self):
		if not self.record.value(self.name):
			return

		# Under windows platforms we need to create the temporary
		# file with an appropiate extension, otherwise the system
		# won't be able to know how to open it. The only way we have
		# to know what kind of file it is, is if the filename property
		# was set, and pick up the extension from that field.
		extension = ''
		if self.fileName() and '.' in self.fileName():
			extension = '.%s' % self.fileName().rpartition('.')[2]
		else:
			extension = ''

		fileName = tempfile.mktemp( extension )
		fp = file(fileName,'wb+')
		fp.write( self.record.value(self.name) )
		fp.close()
		Common.openFile( fileName )

	def showImage(self):
		if not self.record.value(self.name): 
			return
		dialog = QDialog( self )
		dialog.setWindowTitle( _('Image') )
		label = QLabel( dialog )
		pix = QPixmap()
		pix.loadFromData( self.record.value(self.name) )
		label.setPixmap( pix )
		layout = QHBoxLayout( dialog )
		layout.addWidget( label )
		dialog.exec_()

	def new(self):
		filename = QFileDialog.getOpenFileName(self, _('Select the file to attach'), self.baseDirectory, self.filters)
		if filename.isNull():
			return
		filename = unicode(filename)
		self.baseDirectory = os.path.dirname(filename)
		self.setBinaryFile( filename )

	def setBinaryFile(self, filename):
		try:
			value = file(filename, 'rb').read()
		except Exception, e:
			QMessageBox.information(self, _('Error'), _('Error reading the file:\n%s') % unicode(e.args) )
			return

		self.record.setValue( self.name, value )

		# The binary widget might have a 'filename' attribute
		# that stores the file name in the field indicated by 'filename'
		if self.fileNameField:
			self.record.setValue( self.fileNameField, os.path.basename(filename) )
			if self.view:
				self.view.widgets[self.fileNameField].load(self.record)
		self.showValue()

	def fileName(self):
		if self.fileNameField:
			if self.record.fieldExists( self.fileNameField ):
				return self.record.value( self.fileNameField )
		if self.record.fieldExists( 'name' ):
			return self.record.value( 'name' ) or self.name
		return self.name

	def save(self):
		directory = '%s/%s' % (self.baseDirectory, unicode(self.fileName()) )
		filename = QFileDialog.getSaveFileName( self, _('Save as...'), directory, self.filters )
		if filename.isNull():
			return
		filename = unicode(filename)
		self.baseDirectory = os.path.dirname(filename)

		try:
			fp = file(filename,'wb+')
			fp.write( self.record.value(self.name) )
			fp.close()
		except Exception, e:
			QMessageBox.information(self, _('Error'), _('Error writing the file:\n%s') % unicode(e.args) )
			return
		Semantic.addInformationToFile( filename, self.record.group.resource, self.record.id, self.name )

	def remove(self):
		self.record.setValue( self.name, False )
		self.clear()
		self.modified()
		if 'filename' in self.attrs:
			w = self.attrs['filename']
			self.record.setValue( w, False )
			if self.view:
				self.view.widgets[w].load(self.record)

	def showValue(self):
		if self.record.value( self.sizeName ):
			self.setText( self.record.value( self.sizeName ) )
		else:
			self.clear()
		self.updateActions()

	def clear(self):
		self.uiBinary.clear()
		self.updateActions()

	def setText(self, text):
		if text:
			self.uiBinary.setText( text )
		else:
			self.uiBinary.clear()
		self.uiBinary.setCursorPosition( 0 )

	# This widget is a bit special. We don't set the value
	# here. We do it in the new(), so we don't have two copies
	# of the file (which can be pretty big) in memory.
	def storeValue(self):
		pass

	def colorWidget(self):
		return self.uiBinary

	def saveState(self):
		return QByteArray( self.baseDirectory.encode('utf-8') )

	def restoreState(self, value):
		if not value:
			return
		self.baseDirectory = unicode( str( value ), 'utf-8' )
