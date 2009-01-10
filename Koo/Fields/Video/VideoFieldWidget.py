##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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


from Koo.Common import Common

from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
	from PyQt4.phonon import *
except:
	pass


(VideoFieldWidgetUi, VideoFieldWidgetBase) = loadUiType( Common.uiPath('video.ui') ) 

class VideoFieldWidget(AbstractFieldWidget, VideoFieldWidgetUi):
	def __init__(self, parent, view, attrs={}):
		AbstractFieldWidget.__init__(self, parent, view, attrs)
		VideoFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.uiVideo.installPopupenu( self.widget )

		self.connect( self.pushPlay, SIGNAL('clicked()'), self.play )
		self.connect( self.pushPause, SIGNAL('clicked()'), self.pause )
		self.connect( self.pushStop, SIGNAL('clicked()'), self.stop )
		self.connect( self.pushLoad, SIGNAL('clicked()'), self.load )
		self.connect( self.pushSave, SIGNAL('clicked()'), self.save )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.remove )

	def load(self):
		try:
			filename = QFileDialog.getOpenFileName(self, _('Select the file to attach'))
			if filename.isNull():
				return
			filename = unicode(filename)
			value = file(filename).read()
			self.model.setValue( self.name, value )
		except:
			QMessageBox.information(self, '', _('Error reading the file'))

	def save(self):
		try:
			filename = QFileDialog.getSaveFileName( self, _('Save as...') )
			if filename:
				fp = file(filename,'wb+')
				fp.write( self.model.value(self.name) )
				fp.close()
		except:
			QMessageBox.information(self, '', _('Error writing the file!'))
	def remove(self):
		self.model.setValue( self.name, False )
		self.clear()
		self.modified()

	def play(self):
		self.uiVideo.stop()
		value = self.model.value( self.name )
		if not value:
			return
		if self.isUrl( value ):
			media = Phonon.MediaSource( value )
		else:
			media = Phonon.MediaSource( QBuffer( QByteArray( value ) ) )
		self.uiVideo.play( media )

	def pause(self):
		self.uiVideo.pause()

	def stop(self):
		self.uiVideo.stop()

	def store(self):
		pass

	def clear(self):
		self.widget.setText('')
	
	def showValue(self):
		pass

	def setReadOnly(self, value):
		self.pushLoad.setEnabled( not value )

	def isUrl(self, value):
		if len(value) > 500:
			return False
		url = QUrl( value )
		return url.isValid()

