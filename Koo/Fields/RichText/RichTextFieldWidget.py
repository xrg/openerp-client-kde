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
from Koo.Common import Shortcuts
from Koo.Fields.TranslationDialog import *
from Koo.Fields.AbstractFieldWidget import *

(RichTextFieldWidgetUi, RichTextFieldWidgetBase) = loadUiType( Common.uiPath('richtext.ui') ) 

class RichTextFieldWidget(AbstractFieldWidget, RichTextFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		RichTextFieldWidgetUi.__init__(self)
		self.setupUi(self)

		self.setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Expanding )
		self.installPopupMenu( self.uiText )

		self.connect( self.pushBold, SIGNAL('clicked()'), self.bold )
		self.connect( self.pushItalic, SIGNAL('clicked()'), self.italic )
		self.connect( self.pushUnderline, SIGNAL('clicked()'), self.underline )
		self.connect( self.pushStrike, SIGNAL('clicked()'), self.strike )
		self.connect( self.pushLeftJustify, SIGNAL('clicked()'), self.leftJustify )
		self.connect( self.pushCenter, SIGNAL('clicked()'), self.center )
		self.connect( self.pushRightJustify, SIGNAL('clicked()'), self.rightJustify )
		self.connect( self.pushJustify, SIGNAL('clicked()'), self.justify )
		self.connect( self.pushForegroundColor, SIGNAL('clicked()'), self.foregroundColor )
		self.connect( self.pushBackgroundColor, SIGNAL('clicked()'), self.backgroundColor )
		self.connect( self.uiFont, SIGNAL('currentFontChanged(QFont)'), self.font )
		self.connect( self.uiFontSize, SIGNAL('valueChanged(int)'), self.fontSize )
		self.connect( self.uiText, SIGNAL('cursorPositionChanged()'), self.cursorPosition)

		self.updateFont = True
		font = self.uiText.document().defaultFont()
		self.font( font )
		self.fontSize( font.pointSize() )

		if attrs.get('translate', False):
			self.connect( self.pushTranslate, SIGNAL('clicked()'), self.translate )

			self.scTranslate = QShortcut( self.uiText )
			self.scTranslate.setKey( Shortcuts.SearchInField )
			self.scTranslate.setContext( Qt.WidgetShortcut )
			self.connect( self.scTranslate, SIGNAL('activated()'), self.translate )
		else:
			self.pushTranslate.setVisible( False )

	def translate(self):
		if not self.record.id:
			QMessageBox.information( self, _('Translation dialog'), _('You must save the resource before adding translations'))
			return

		html = Common.simplifyHtml( self.uiText.document().toHtml() )
		dialog = TranslationDialog( self.record.id, self.record.group.resource, self.attrs['name'], html, TranslationDialog.RichEdit, self )
		if dialog.exec_() == QDialog.Accepted:
			self.record.setValue(self.name, unicode( dialog.result ) or False )

	def updateCurrentColors(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		# Foreground color
		p = QPixmap( QSize(40, 10) )
		p.fill( format.foreground().color() )
		self.pushForegroundColor.setIcon( QIcon(p) )
		# Background color
		p = QPixmap( QSize(40, 40) )
		p.fill( format.background().color() )
		self.pushBackgroundColor.setIcon( QIcon(p) )
		
	def foregroundColor(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		color = QColorDialog.getColor( format.foreground().color(), self )
		format.setForeground( QBrush( color ) )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()
		self.updateCurrentColors()

	def backgroundColor(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		color = QColorDialog.getColor( format.background().color(), self )
		format.setBackground( QBrush( color ) )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()
		self.updateCurrentColors()
		
	def cursorPosition(self):
		align = self.uiText.alignment() 
		if align == Qt.AlignLeft:
			self.pushLeftJustify.setChecked( True )
		elif align == Qt.AlignHCenter:
			self.pushCenter.setChecked( True )
		elif align == Qt.AlignRight:
			self.pushRightJustify.setChecked( True )
		else:
			self.pushJustify.setChecked( True )
		self.charFormatChanged( self.uiText.currentCharFormat() )

	def charFormatChanged(self, format):
		font = format.font()
		self.updateFont = False
		self.uiFont.setCurrentFont( font )
		self.uiFontSize.setValue( font.pointSize() )
		self.pushBold.setChecked( font.weight() == QFont.Bold )
		self.pushUnderline.setChecked( font.underline() )
		self.pushItalic.setChecked( font.italic() )
		self.pushStrike.setChecked( font.strikeOut() )
		self.updateCurrentColors()
		self.updateFont = True

	def fontSize(self, size):
		if not self.updateFont:
			return
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		format.setFontPointSize( size )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()

	def font(self, font):
		if not self.updateFont:
			return
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		format.setFont( font )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()
		
	def bold(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		if format.fontWeight() == QFont.Bold:
			format.setFontWeight( QFont.Normal )
		else:
			format.setFontWeight( QFont.Bold )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()

	def italic(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		format.setFontItalic( not format.fontItalic() )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()

	def underline(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		format.setFontUnderline( not format.fontUnderline() )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()

	def strike(self):
		cursor = self.uiText.textCursor()
		format = cursor.charFormat()
		format.setFontStrikeOut( not format.fontStrikeOut() )
		cursor.setCharFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()

	def leftJustify(self):
		self.setAlignment( Qt.AlignLeft )

	def center(self):
		self.setAlignment( Qt.AlignHCenter )

	def rightJustify(self):
		self.setAlignment( Qt.AlignRight )

	def justify(self):
		self.setAlignment( Qt.AlignJustify )

	def setAlignment(self, align):
		cursor = self.uiText.textCursor()
		format = cursor.blockFormat()
		format.setAlignment( align )
		cursor.setBlockFormat( format )
		self.uiText.setTextCursor( cursor )
		self.uiText.setFocus()
		
	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		self.uiText.setReadOnly( value )
		self.pushBold.setEnabled( not value )
		self.pushItalic.setEnabled( not value )
		self.pushUnderline.setEnabled( not value )
		self.pushStrike.setEnabled( not value )
		self.pushLeftJustify.setEnabled( not value )
		self.pushCenter.setEnabled( not value )
		self.pushRightJustify.setEnabled( not value )
		self.pushJustify.setEnabled( not value )
		self.pushForegroundColor.setEnabled( not value )
		self.pushBackgroundColor.setEnabled( not value )
		self.uiFont.setEnabled( not value )
		self.uiFontSize.setEnabled( not value )

	def colorWidget(self):
		return self.uiText

	def storeValue(self):
		# As the HTML returned can be different than the one we set in 
		# showValue() even if the text hasn't been modified by the user
		# we need to track modifications using QTextDocument property
		if self.uiText.document().isModified():
			html = Common.simplifyHtml( self.uiText.document().toHtml() )
			self.record.setValue(self.name, html or False )

	def clear(self):
		self.uiText.setHtml('')

	def showValue(self):
		value = self.record.value(self.name)
		if not value:
			value=''
		self.uiText.setHtml( value )
		# As the HTML returned can be different than the one we set in 
		# showValue() even if the text hasn't been modified by the user
		# we need to track modifications using QTextDocument property
		self.uiText.document().setModified( False )
