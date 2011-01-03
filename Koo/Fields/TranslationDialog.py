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

from Koo import Rpc
from Koo.Common import Common
from Koo.Model.Group import RecordGroup

import copy

(TranslationDialogUi, TranslationDialogBase) = loadUiType( Common.uiPath('translationdialog.ui') ) 

## @brief TranslationDialog class provides a dialog for translating the value of a
# translatable field.
class TranslationDialog( QDialog, TranslationDialogUi ):
	LineEdit = 0
	TextEdit = 1
	RichEdit = 2

	## @brief Constructs a new TranslationDialog object.
	def __init__(self, id, model, fieldName, value, type, parent = None):
		QDialog.__init__(self, parent)
		TranslationDialogUi.__init__(self)
		self.setupUi( self )

		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.id = id
		self.model = model
		self.fieldName = fieldName
		self.value = value
		self.type = type

		self.values = {}
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

		arch = []
		fields = {}
		for lang in languages:
			if self.type == TranslationDialog.LineEdit:
				widget = 'char'
				fieldType = 'char'
			elif self.type == TranslationDialog.TextEdit:
				widget = 'text'
				fieldType = 'text'
			else:
				widget = 'text_tag'
				fieldType = 'text'

			arch.append( """<field name="%s" widget="%s" use="{'lang':'%s'}"/>""" % (lang['code'], widget, lang['code']) )
			fields[lang['code']] = {
				'string': lang['name'],
				'type': fieldType,
			}
			if lang['code'] == self.currentCode:
				self.values[ lang['code'] ] = self.value
				continue

			context = copy.copy(Rpc.session.context)			
			context['lang'] = self.adaptContext( lang['code'] )
			val = Rpc.session.execute( '/object', 'execute', self.model, 'read', [self.id], [self.fieldName], context)
			val = val[0]

			self.values[ lang['code'] ] = val[self.fieldName]

		arch = '<form string="%s" col="2">%s</form>' % (_('Translation Dialog'), ''.join( arch ) )

		self.group = RecordGroup( 'translator' )
		# Do not allow record loading as most probably 'wizard.'+name model
		# won't exist in the server
		self.group.setDomainForEmptyGroup()
		self.uiScreen.setRecordGroup( self.group )
		self.uiScreen.new(default=False)
		self.uiScreen.addView(arch, fields, display=True)
		self.uiScreen.currentRecord().set(self.values)
		self.uiScreen.display()

	def slotAccept(self):
		self.uiScreen.currentView().store()
		for lang, oldValue in self.values.iteritems():
			newValue = self.uiScreen.currentRecord().value( lang )
			# Don't update on the server the current text. This would cause information
			# on the server to be updated after the form has been read causing possible
			# conflits.
			if lang == self.currentCode:
				self.result = newValue
				continue
			# Only update on the server if the value has changed
			if newValue == oldValue:
				continue
			context = copy.copy(Rpc.session.context)
			context['lang'] = self.adaptContext( lang )
			Rpc.session.execute( '/object', 'execute', self.model, 'write', [self.id], {self.fieldName: newValue}, context )
		self.accept()

