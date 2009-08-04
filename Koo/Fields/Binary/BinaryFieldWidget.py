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

(BinaryFieldWidgetUi, BinaryFieldWidgetBase) = loadUiType( Common.uiPath('binary.ui') ) 

class BinaryFieldWidget(AbstractFieldWidget, BinaryFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		BinaryFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.filters = attrs.get('filters', '*')
		self.filters = self.filters.split(',')
		self.filters = _('Files (%s)') % ' '.join( self.filters )

		self.fileNameField = attrs.get('filename')
		self.dialogFileNameField = attrs.get('name')

		self.connect( self.pushNew, SIGNAL('clicked()'), self.new )
		self.connect( self.pushRemove, SIGNAL('clicked()'),self.remove )

		self.actionSave = QAction(self)
		self.actionSave.setText( _('&Save') )
		self.actionSave.setIcon( QIcon( ':/images/save.png' ) )
		self.actionOpen = QAction(self)
		self.actionOpen.setText( _('&Open') )
		self.actionOpen.setIcon( QIcon( ':/images/open.png' ) )
		self.actionShowImage = QAction(self)
		self.actionShowImage.setText( _('Show &image'), )
		self.actionShowImage.setIcon( QIcon( ':/images/convert.png' ) )

		self.menu = QMenu( self )
		self.menu.addAction( self.actionSave )
		self.menu.addAction( self.actionOpen )
		self.menu.addAction( self.actionShowImage )
		self.pushSave.setMenu( self.menu )
		self.pushSave.setDefaultAction( self.actionSave )

		self.connect( self.actionSave, SIGNAL('triggered()'), self.save )
		self.connect( self.actionOpen, SIGNAL('triggered()'), self.open )
		self.connect( self.actionShowImage, SIGNAL('triggered()'), self.showImage )
		self.connect( self.menu, SIGNAL('aboutToShow()'), self.updateShowImageAction )

		self.installPopupMenu( self.uiBinary )
		
	def setReadOnly(self, value):
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
		if self.record and self.record.value(self.name):
			enable = True
		else:
			enable = False
		self.actionSave.setEnabled( enable )
		self.actionOpen.setEnabled( enable )
		self.actionShowImage.setEnabled( enable )

	def menuEntries(self):
		if self.record.value(self.name):
			enableApplication = True
		else:
			enableApplication = False

		pix = QPixmap()
		if pix.loadFromData( self.record.value(self.name) ):
			enableImage = True
		else:
			enableImage = False
		return [ (_('Open...'), self.open, enableApplication), 
			 (_('Show &image...'), self.showImage, enableImage) ]

	def open(self):
		if not self.record.value(self.name):
			return

		# Under windows platforms we need to create the temporary
		# file with an appropiate extension, otherwise the system
		# won't be able to know how to open it. The only way we have
		# to know what kind of file it is, is if the filename property
		# was set, and pick up the extension from that field.
		extension = ''
		if self.fileName():
			extension = '.%s' % self.fileName().rpartition('.')[2]

		fileName = tempfile.mktemp( extension )
		fp = file(fileName,'wb+')
		fp.write( self.record.value(self.name) )
		fp.close()
		Common.openFile( fileName )

	def showImage(self):
		if not self.record.value(self.name): 
			return
		dialog = QDialog( self )
		label = QLabel( dialog )
		pix = QPixmap()
		pix.loadFromData( self.record.value(self.name) )
		label.setPixmap( pix )
		layout = QHBoxLayout( dialog )
		layout.addWidget( label )
		dialog.exec_()

	def new(self):
		filename = QFileDialog.getOpenFileName(self, _('Select the file to attach'), QDir.homePath(), self.filters)
		if filename.isNull():
			return
		filename = unicode(filename)
		try:
			value = file(filename, 'rb').read()
		except Exception, e:
			QMessageBox.information(self, _('Error'), _('Error reading the file:\n%s') % unicode(e.args) )
			return

		self.record.setValue( self.name, value )
		self.uiBinary.setText( _('%d bytes') % len(value) )

		# The binary widget might have a 'filename' attribute
		# that stores the file name in the field indicated by 'filename'
		if self.fileNameField:
			self.record.setValue( self.fileNameField, os.path.basename(filename) )
			if self.view:
				self.view.widgets[self.fileNameField].load(self.record)
		self.updateActions()

	def fileName(self):
		if self.fileNameField:
			return self.record.value( self.fileNameField )
		if self.dialogFileNameField:
			return self.record.value( self.dialogFileNameField )
		return ''
		
	def save(self):
		directory = '%s/%s' % (QDir.homePath(), self.fileName() )
		filename = QFileDialog.getSaveFileName( self, _('Save as...'), directory, self.filters )
		if filename.isNull():
			return
		filename = unicode(filename)
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
		if self.record.value( self.name ):
			size = len( self.record.value( self.name ) )
			self.uiBinary.setText( _('%d bytes') % size ) 
		else:
			self.clear()
		self.updateActions()

	def clear(self):
		self.uiBinary.clear()
		self.updateActions()

	# This widget is a bit special. We don't set the value
	# here. We do it in the new(), so we don't have two copies
	# of the file (which can be pretty big) in memory.
	def store(self):
		pass

	def colorWidget(self):
		return self.uiBinary

