from PyQt4.QtGui import *
from PyQt4.QtCore import *
import rpc

class ToolBar(QToolBar):
	def __init__(self, parent=None):
		QToolBar.__init__(self, parent)
		self.setOrientation( Qt.Vertical )
		self.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
		self.actions = {}
		self.loaded = False

	def setup(self, actions):
		if self.loaded:
			return
		self.loaded = True
		last = None
		for action in actions:
			if last and last != action.type():
				self.addSeparator()
			last = action.type()
			self.addAction( action )
		
