from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
import askserver
from common import common
import options
import rpc
import re

class CreationOkDialog( QDialog ):
	def __init__(self, passwordList, parent=None ):
		QDialog.__init__(self, parent)

		loadUi( common.uiPath('dbcreateok.ui'), self ) 
		self.connect( self.pushConnect, SIGNAL('clicked()'), self.connectNow )
		self.connect( self.pushLater, SIGNAL('clicked()'), self.connectLater )

		self.textEdit.setPlainText( _('The following users have been installed on your database:\n\n'+ passwordList + '\n\n'+_('You can now connect to the database as an administrator.') ) )
		self.show()

	def connectLater(self):
		self.reject()

	def connectNow(self):
		self.accept()

class ProgressBar( QDialog ):
	def __init__(self, parent=None ):
		QDialog.__init__(self, parent )
		loadUi( common.uiPath('progress.ui'), self ) 
		self.setModal( True )
		self.timer = QTimer( self )
		self.connect(self.timer,SIGNAL("timeout()"),self.timeout)
		self.url = ""
		self.databaseName = ""
		self.demoData = ""
		self.language = ""
		self.password = ""
		self.show()

	def start(self):
		try:
			self.id = rpc.database.execute(self.url, 'create', self.password, self.databaseName, self.demoData, self.language)
			self.timer.start( 1000 )
		except Exception, e:
			if e.faultString=='AccessDenied:None':
				QMessageBox.warning(self,_("Could not create database."), _('Bad database administrator password !'))
			else:
				QMessageBox.warning(self, _('Error during database creation !'),_("Could not create database."))

	def timeout(self):
		try:
			progress,users = rpc.database.call(self.url, 'get_progress', self.password, self.id)
		except:
			self.timer.stop()
			QMessageBox.warning(self,_("Error during database creation !"),_("The server crashed during installation.\nWe suggest you to drop this database."))
			self.reject()

		if 0.0 <= progress < 1.0:
			self.progressBar.setValue(progress * 100)
		elif progress == 1.0:
			self.progressBar.setValue(100)
			self.timer.stop()
			pwdlst = '\n'.join(map(lambda x: '    - %s: %s / %s' % (x['name'],x['login'],x['password']), users))
			dialog = CreationOkDialog( pwdlst, self )
			r = dialog.exec_()
			# Propagate the result of the dialog. If the user wants to connect return
			# Accepted, otherwise return Rejected
			self.done( r )


class CreateDatabaseDialog( QDialog ):
	def __init__(self, parent=None ):
		QDialog.__init__(self, parent)
		loadUi( common.uiPath('create_database.ui'), self ) 
		self.connect(self.pushCancel,SIGNAL("clicked()"),self.slotCancel )
		self.connect(self.pushAccept,SIGNAL("clicked()"),self.slotAccept )
		self.connect(self.pushChange,SIGNAL("clicked()"),self.slotChange )

		url = '%s%s:%s' % (options.options['login.protocol'], options.options['login.server'], options.options['login.port'])
		self.tinyServer.setText(url)
		self.refreshLangList(url) 
	
	def refreshLangList(self, url):
		self.language.clear()
		lang_list = rpc.database.call(url, 'list_lang')
		lang_list.append( ('en_US','English') )
		for key,val in lang_list:
			self.language.addItem( val, QVariant( key ) )
		self.language.setCurrentIndex( self.language.count() - 1 )

	def slotCancel(self):
		self.close()
	
	def slotAccept(self):
		databaseName = str( self.database.text() )
		if ((not databaseName) or (not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', databaseName))):
			QMessageBox.warning( self, _('Bad database name !'), _('The database name must contain only normal characters or "_".\nYou must avoid all accents, space or special characters.') )
		demoData = self.demoData.isChecked()

		langreal = str( self.language.itemData( self.language.currentIndex() ).toString() )
		passwd = str( self.password.text() )
		url = str( self.tinyServer.text() )

		progress = ProgressBar()
		progress.url = url
		progress.databaseName = databaseName
		progress.demoData = demoData
		progress.language = langreal 
		progress.password = passwd 
		progress.start()
		r = progress.exec_()

		if r == QDialog.Accepted:
			m = QUrl( url )
			m.setUserName( 'admin' )
			m.setPassword( 'admin' )
			self.url = unicode( m.toString() )
			self.databaseName = databaseName
		self.done( r )

	def slotChange(self):
		dialog = askserver.AskServer( self )
		dialog.setDefault( str( self.tinyServer.text() ) )
		ret = dialog.exec_()
		if ret == QDialog.Accepted:
			url = dialog.url
			self.tinyServer.setText( url )
			try:
				if self.language:
					self.refreshLangList(url)
				self.pushAccept.setEnabled(True)
			except:
				self.pushAccept.setEnabled(False)

