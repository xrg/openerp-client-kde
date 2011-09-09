##############################################################################
#
# Copyright (c) 2007-2010 Albert Cervera i Areny <albert@nan-tic.com>
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

from PyQt4.QtCore  import  *
from PyQt4.QtGui import *
from Common.Ui import *

from Koo.Common.Settings import *
from Koo.Common.Paths import *

Tips = [
_("""
<p>
<b>Welcome to Koo!</b>
</p>
<p>
Koo is a client that gives you access to the powerful OpenERP application with
very good performance and bleeding edge features.
</p>
"""),
_("""
<p>
<b>Integrated calculator</b>
</p>
<p>
Did you know that you can use number input boxes like a calculator? Go to a field where you should insert a number and type <i>3+4*12</i>. Then press enter to see the result or store the form directly. In both cases you will see the result updated in the same input box. Allowed operators include: +, -, *, / and you can also use parenthesis.
</p>
"""),
_("""
<p>
<b>Full Text Search</b>
</p>
<p>
Did you know that you can search any record of your database from a single place, just like you do with Google? Search and install the full_text_search module and follow the instructions on how to configure it properly.
</p>
"""),
_("""
<p>
<b>Export information</b>
</p>
<p>
Did you know that you can easily export OpenERP information? Go to Form and then Export Data. You can even store your preferences and use it easily as many times as you need.
</p>
"""),
]

(TipOfTheDayDialogUi, TipOfTheDayDialogBase) = loadUiType( uiPath('tip.ui') )

## @brief The TipOfTheDayDialog class shows a dialog with a Tip of the day
class TipOfTheDayDialog( QDialog, TipOfTheDayDialogUi ):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		TipOfTheDayDialogUi.__init__(self)
		self.setupUi( self )

		try:
			self.number = int( Settings.value('tip.position') )
		except:
			self.number = 0

		self.connect( self.pushNext, SIGNAL('clicked()'), self.nextTip )
		self.connect( self.pushPrevious, SIGNAL('clicked()'), self.previousTip )
		self.connect( self.pushClose, SIGNAL('clicked()'), self.closeTip )
		self.uiShowNextTime.setChecked( Settings.value('tip.autostart') )
		self.showTip()
	
	def showTip(self):
		self.uiTip.setText( Tips[ self.number % len(Tips) ] )

	def nextTip(self):
		self.number += 1
		self.showTip()

	def previousTip(self):
		self.number -= 1
		self.showTip()

	def closeTip(self):
		Settings.setValue( 'tip.autostart', self.uiShowNextTime.isChecked() )
		Settings.setValue( 'tip.position', self.number + 1 )
		Settings.saveToFile()
		self.close()

