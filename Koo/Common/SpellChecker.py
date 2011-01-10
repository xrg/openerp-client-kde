##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
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

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import Debug

try:
	from enchant.checker import SpellChecker
	import enchant

	enchantAvailable = True
except:
	Debug.info(_('Enchant spell checker library not found. Consider installing it if you want Koo to spell check your text boxes.'))
	enchantAvailable = False
	

## @brief The SpellCheckHighlighter class highlights invalid words for a given language using
# enchant spell checker library.
class SpellCheckHighlighter(QSyntaxHighlighter):
	def __init__(self, parent, language):
		QSyntaxHighlighter.__init__(self, parent)
		self._language = language
		if not enchantAvailable:
			self._checker = None
			return
		try:
			self._checker = SpellChecker(self._language)
		except enchant.DictNotFoundError: 
			self._checker = None
			Debug.info(_('SpellChecking: No dictionary available for language "%s"') % self._language)

		self._format = QTextCharFormat()
		self._format.setUnderlineColor(QColor(Qt.red));
		self._format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline);

	def highlightBlock(self, text):
		if not enchantAvailable or not self._checker:
			return

		text = unicode(text)
		self._checker.set_text( text )
		for error in self._checker:
			self.setFormat(error.wordpos, len(error.word), self._format)

