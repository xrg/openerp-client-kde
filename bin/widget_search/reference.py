from abstractsearchwidget import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from common import common

class ReferenceSearchWidget(AbstractSearchWidget):
	def __init__(self, name, parent, attrs={}):
		AbstractSearchWidget.__init__(self, name, parent, attrs)
		loadUi( common.uiPath('searchreference.ui'), self )
		self.setPopdown( attrs.get('selection',[]) )
		self.focusWidget = self.uiModel

	def setPopdown(self, selection):
		self.invertedModels = {}

		for (i,j) in selection:
			self.uiModel.addItem( j, QVariant(i) )
			self.invertedModels[i] = j

	def getValue(self):
		resource = unicode(self.uiModel.itemData(self.uiModel.currentIndex()).toString())
		if resource:
			return [(self.name, 'like', resource + ',')]
		else:
			return []


	def setValue(self, value):
		model, (id, name) = value
		self.uiModel.setCurrentIndex( self.uiModel.findText(self.invertedModels[model]) )

	value = property(getValue, setValue, None,
	  'The content of the widget or ValueError if not valid')

	def clear(self):
		self.value = ''


