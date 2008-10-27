##############################################################################
#
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
from ServerConfigurationDialog import *
from Common import Options
import Rpc

class AdministratorPasswordDialog( QDialog ):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi(Common.uiPath('admin_passwd.ui'), self)
		self.connect( self.pushChange, SIGNAL('clicked()'), self.slotChange )	
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		host = Options.options['login.server']
		port = Options.options['login.port']
		secure = Options.options['login.secure']
		protocol = secure and 'https' or 'http'
		url = '%s://%s:%s' % (protocol, host, port)
		self.uiServer.setText(url)

	def slotChange(self):
		dialog = ServerConfigurationDialog( self )
		dialog.setDefault( str( self.uiServer.text() ) )
		dialog.exec_()
		self.uiServer.setText( dialog.url )

	def slotAccept(self):
		if self.uiNewPassword.text() != self.uiConfirmationPassword.text():
			QMessageBox.warning(self, _('Validation Error'), _('Confirmation password does not match new password.') )
			return
		try:
			url = str(self.uiServer.text())
			old = str(self.uiOldPassword.text())
			new = str(self.uiNewPassword.text())
			Rpc.database.call(url, 'change_admin_password', old, new)
			QMessageBox.information(self, '', _('Password changed successfully') )
			self.accept()
		except Exception,e:
			QMessageBox.warning(self,_('Error'), _('Could not change administrator password. Please, check the server and password are correct.'))

