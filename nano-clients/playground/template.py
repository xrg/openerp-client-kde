from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class Template:
	def __init__(self, name):
		self.name = name
		self.boxes = []

	def addBox(self, box):
		self.boxes.append( box )

class TemplateBox:
	def __init__(self):
		self.rect = QRectF()

class TemplateMatcherBox(TemplateBox):
	def __init__(self):
		TemplateBox.__init__(self)
		self.text = ''

class TemplateInputBox(TemplateBox):
	def __init__(self):
		TemplateBox.__init__(self)

