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

from Koo.Common import Shortcuts

from Koo.Fields.TranslationDialog import *
from Koo.Fields.AbstractFieldWidget import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class TextBoxFieldWidget(AbstractFieldWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		self.uiText = QTextEdit( self )
		self.uiText.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Expanding )
		self.uiText.setTabChangesFocus( True )
		self.uiText.setAcceptRichText( False )
		self.installPopupMenu( self.uiText )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiText )
		if attrs.get('translate', False):
			pushTranslate = QToolButton( self )
			pushTranslate.setIcon( QIcon( ':/images/locale.png' ) )
			pushTranslate.setFocusPolicy( Qt.NoFocus )
			layout.addWidget( pushTranslate )
			self.connect( pushTranslate, SIGNAL('clicked()'), self.translate )

			self.scTranslate = QShortcut( self.uiText )
			self.scTranslate.setKey( Shortcuts.SearchInField )
			self.scTranslate.setContext( Qt.WidgetShortcut )
			self.connect( self.scTranslate, SIGNAL('activated()'), self.translate )

	def translate(self):
		if not self.record.id:
			QMessageBox.information( self, _('Translation dialog'), _('You must save the resource before adding translations'))
			return
		dialog = TranslationDialog( self.record.id, self.record.group.resource, self.attrs['name'], unicode(self.uiText.toPlainText()), TranslationDialog.TextEdit, self )
		if dialog.exec_() == QDialog.Accepted:
			self.uiText.setPlainText( dialog.result )

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		self.uiText.setReadOnly( value )

	def colorWidget(self):
		return self.uiText

	def store(self):
		self.record.setValue(self.name, unicode( self.uiText.document().toPlainText() ) or False )

	def clear(self):
		self.uiText.clear()

	def showValue(self):
		vScroll = self.uiText.verticalScrollBar().value()
		hScroll = self.uiText.horizontalScrollBar().value()
		position = self.uiText.textCursor().position()
		value = self.record.value(self.name)
		if not value:
			self.uiText.clear()
		else:
			self.uiText.setPlainText( value )
		cursor = self.uiText.textCursor()
		cursor.setPosition( position )
		self.uiText.setTextCursor( cursor )
		self.uiText.verticalScrollBar().setValue( vScroll )
		self.uiText.horizontalScrollBar().setValue( hScroll )

