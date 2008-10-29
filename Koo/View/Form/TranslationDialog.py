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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from Koo.Common import Common
import copy
from Koo import Rpc

class TranslationDialog( QDialog ):
	LineEdit = 0
	TextEdit = 1

	def __init__(self, id, model, fieldName, value, type, parent = None):
		QDialog.__init__(self, parent)
		loadUi( Common.uiPath('translationdialog.ui'), self )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.setWindowTitle( _('Translation Dialog') )
		self.id = id
		self.model = model
		self.fieldName = fieldName
		self.value = value
		self.type = type

		self.translations = []
		self.result = value
		# Using the timer should improve user feedback
		QTimer.singleShot( 0, self.init )

	def adaptContext(self, value):
		if value == 'en_US':
			return False
		else:
			return value

	def init(self):
		self.currentCode = Rpc.session.context.get('lang', 'en_US')

		languageIds = Rpc.session.execute( '/object', 'execute', 'res.lang', 'search', [('translatable','=','1')])
		languages = Rpc.session.execute( '/object', 'execute', 'res.lang', 'read', languageIds, ['code', 'name'] )
		languages.append( {'code': 'en_US', 'name': 'English'} )

		layout = QGridLayout()
		self.layout().insertLayout(0, layout)
		for lang in languages:
			uiLabel = QLabel( lang['name'] + ':', self)
			if self.type == TranslationDialog.LineEdit:
				uiText = QLineEdit(self)
			else:
				uiText = QTextEdit(self)

			row = layout.rowCount() + 1
			layout.addWidget( uiLabel, row, 0 )
			layout.addWidget( uiText, row, 1 )

			if lang['code'] == self.currentCode:
				uiText.setText( self.value )
				self.translations.append( { 'code': lang['code'], 'widget': uiText, 'value': self.getText(uiText) } )
				continue

			context = copy.copy(Rpc.session.context)			
			context['lang'] = self.adaptContext( lang['code'] )
			val = Rpc.session.execute( '/object', 'execute', self.model, 'read', [self.id], [self.fieldName], context)
			val = val[0]
			uiText.setText( val[self.fieldName] or '' )
			self.translations.append( { 'code': lang['code'], 'widget': uiText, 'value': self.getText(uiText) } )

	def getText(self, widget):
		if self.type == TranslationDialog.LineEdit:
			return unicode(widget.text())
		else:
			return unicode(widget.document().toPlainText())
		
	def slotAccept(self):
		for lang in self.translations:
			newValue = self.getText( lang['widget'] )
			# Don't update on the server the current text. This would cause information
			# on the server to be updated after the form has been read causing possible
			# conflits.
			if lang['code'] == self.currentCode:
				self.result = newValue
				continue
			# Only update on the server if the value has changed
			if newValue == lang['value']:
				continue
			context = copy.copy(Rpc.session.context)
			context['lang'] = self.adaptContext( lang['code'] )
			Rpc.session.execute( '/object', 'execute', self.model, 'write', [self.id], {self.fieldName: newValue}, context )
		self.accept()

