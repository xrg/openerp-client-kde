from PyQt4.QtCore import *
from PyQt4.QtGui import *
from abstractformwidget import *
from common import api
from common import notifier
from common import icons

class ButtonFormWidget( AbstractFormWidget ):
	def __init__(self, parent, view, attributes) :
		AbstractFormWidget.__init__( self, parent, view, attributes )

		self.button = QPushButton( self )
		layout = QHBoxLayout(self)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget( self.button )

		self.button.setText( attributes.get('string', 'unknown' ) )
		if 'icon' in attributes:
			self.button.setIcon( icons.kdeIcon( attributes['icon'] ))
	
		self.connect( self.button, SIGNAL('clicked()'), self.click)

	def click( self ): 
		# TODO: Remove screen dependency and thus ViewForm.screen
		screen = self.view.screen
		self.view.store()
		if self.model.validate():
			id = screen.save_current()
			if not self.attrs.get('confirm',False) or \
					QMessageBox.question(self,_('Question'),self.attrs['confirm'],QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
				type = self.attrs.get('type', 'workflow')
				if type == 'workflow':
					rpc.session.execute('/object', 'exec_workflow', screen.name, self.name, id)
				elif type == 'object':
					rpc.session.execute('/object', 'execute', screen.name, self.name, [id], self.model.context())
				elif type == 'action':
					action_id = int(self.attrs['name'])
					api.instance.execute(action_id, {'model':screen.name, 'id': id, 'ids': [id]})
				else:
					raise 'Button type not allowed'
				screen.reload()
		else:
			notifier.notifyWarning('',_('Invalid Form, correct red fields!'))
			screen.display()

	def setReadOnly(self, value):
		self.button.setEnabled( not value )

	def display(self, state):
		if self.attrs.get('states', False):
			states = self.attrs.get('states', '').split(',')
			if state not in states:
				self.hide()
			else:
				self.show()
		else:
			self.show()


