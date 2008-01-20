from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from askserver import *
import options
import rpc

class ChangeAdministratorPassword( QDialog ):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi(common.uiPath('admin_passwd.ui'), self)
		self.connect( self.pushChange, SIGNAL('clicked()'), self.slotChange )	
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		host = options.options['login.server']
		port = options.options['login.port']
		secure = options.options['login.secure']
		protocol = secure and 'https' or 'http'
		url = '%s://%s:%s' % (protocol, host, port)
		self.uiServer.setText(url)

	def slotChange(self):
		dialog = askserver.AskServer( self )
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
			rpc.database.execute(url, 'change_admin_password', old, new)
			QMessageBox.information(self, '', _('Password changed successfully') )
			self.accept()
		except Exception,e:
			QMessageBox.warning(self,_('Error'), _('Could not change administrator password. Please, check the server and password are correct.'))

