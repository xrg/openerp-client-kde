from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from common import common

class GoToIdDialog( QDialog ):
	def __init__( self, parent=None ):
		QDialog.__init__(self, parent)
		loadUi( common.uiPath('gotoid.ui'), self )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )

	def slotAccept( self ):
		self.result = self.uiId.value()
		self.accept()	

