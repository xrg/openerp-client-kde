from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class Template:
	def __init__(self, name):
		self.name = name
		self.boxes = []

	def addBox(self, box):
		self.boxes.append( box )

class TemplateBox:
	types = ['matcher','input']
	filters = ['none','numeric','alphabetic','alphanumeric']

	def __init__(self):
		self.rect = QRectF()
		self.type = 'matcher'
		self.filter = 'none'
		self.name = ''
		self.text = '' 
	
	def setType(self, value):
		if value not in TemplateBox.types:
			raise "Type '%s' not valid" % value 
		self._type = value
	def getType(self):
		return self._type
	type=property(getType,setType)

	def setFilter(self, value):
		if value not in TemplateBox.filters:
			raise "Filter '%s' not valid" % value
		self._filter = value
	def getFilter(self):
		return self._filter
	type=property(getFilter,setFilter)
	
class Document:
	def __init__(self):
		self.name = ''
		self.template = None
		self.boxes = []

	def addBox(self, box):
		self.boxes.append( box )

class DocumentBox:
	def __init__(self):
		self.text = '' 
		self.templateBox = None

