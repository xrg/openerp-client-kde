from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
import askserver
from common import common
from common import options
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
		self.progressBar.setMinimum( 0 )
		self.progressBar.setMaximum( 0 )
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

		
		# While progress will be 0.0 we'll keep the moving (undefined) progress bar.
		# once it's different we allow it to progress normally. This is done because
		# currently no intermediate values exist.
		if progress > 0.0:
			print "Progress > 0.0"
			self.progressBar.setMaximum( 100 )
			
		if 0.0 < progress < 1.0:
			self.progressBar.setValue(progress * 100)
		elif progress == 1.0:
			self.progressBar.setMaximum( 100 )
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
		self.uiServer.setText(url)
		self.refreshLangList(url) 
	
	def refreshLangList(self, url):
		self.uiLanguage.clear()
		try:
			lang_list = rpc.database.call(url, 'list_lang')
		except:
			self.setDialogEnabled( False )
			return
		lang_list.append( ('en_US','English') )
		for key,val in lang_list:
			self.uiLanguage.addItem( val, QVariant( key ) )
		self.uiLanguage.setCurrentIndex( self.uiLanguage.count() - 1 )
		self.setDialogEnabled( True )

	def setDialogEnabled(self, value):
		if not value:
			self.uiMessage.show()
		else:
			self.uiMessage.hide()
		self.uiPassword.setEnabled( value )
		self.uiDatabase.setEnabled( value )
		self.uiDemoData.setEnabled( value )
		self.uiLanguage.setEnabled( value )
		self.pushAccept.setEnabled( value )

	def slotCancel(self):
		self.close()
	
	def slotAccept(self):
		databaseName = unicode( self.uiDatabase.text() )
		if ((not databaseName) or (not re.match('^[a-zA-Z][a-zA-Z0-9_]+$', databaseName))):
			QMessageBox.warning( self, _('Bad database name !'), _('The database name must contain only normal characters or "_".\nYou must avoid all accents, space or special characters.') )
		demoData = self.uiDemoData.isChecked()

		langreal = unicode( self.uiLanguage.itemData( self.uiLanguage.currentIndex() ).toString() )
		passwd = unicode( self.uiPassword.text() )
		url = unicode( self.uiServer.text() )

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
		dialog.setDefault( str( self.uiServer.text() ) )
		ret = dialog.exec_()
		if ret == QDialog.Accepted:
			url = dialog.url
			self.uiServer.setText( url )
			self.refreshLangList(url)

