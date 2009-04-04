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

import base64
import os
import tempfile

from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from Koo.Common import Common

(LinkFieldWidgetUi, LinkFieldWidgetBase) = loadUiType( Common.uiPath('link.ui') ) 

class LinkFieldWidget(AbstractFieldWidget, LinkFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		LinkFieldWidgetUi.__init__(self)
		self.setupUi(self)
		self.connect( self.pushOpen, SIGNAL('clicked()'), self.open )
		self.installPopupMenu( self.uiText )
		
	def setReadOnly(self, value):
		self.uiText.setEnabled( not value )
		self.pushOpen.setEnabled( not value )

	def menuEntries(self):
		pix = QPixmap()
		if self.record.value(self.name):
			enableApplication = True
		else:
			enableApplication = False

		return [ (_('Open...'), self.openApplication, enableApplication) ]

	def openApplication(self):
		fileName = self.record.value(self.name)
		if not fileName:
			return
		Common.openFile( fileName )

	def open(self):
		filename = QFileDialog.getOpenFileName(self, _('Select the file to link to'))
		if filename.isNull():
			return
		self.record.setValue(self.name, unicode(filename) )

	def showValue(self):
		value = self.record.value( self.name )
		if value:
			self.uiText.setText( value )
		else:
			self.clear()

	def clear(self):
		self.uiText.clear()

	# Value is stored when selected
	def store(self):
		pass

	def colorWidget(self):
		return self.uiText

