##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: parser.py 4698 2006-11-27 12:30:44Z ced $
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

modules = {}
errors = {}

import locale
from common import common

from chartview import *

import sys
try:
	from chart import *
	modules['chart'] = True
except Exception, e:
	errors['chart'] = e
	#print sys.exc_info()
	#print "Can't load charts"

from widget.view.abstractparser import *
from widget.view.form.abstractformwidget import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class EmptyGraph(AbstractFormWidget):
	def __init__(self, model, axis, fields, axis_data={}, attrs={},parent=None):
		AbstractFormWidget.__init__( self, parent, model,attrs )

	def display(self, models):
		pass

class ChartParser( AbstractParser ):

	def create(self, parent, viewModel, node, fields):
		self.viewModel = viewModel
		self.parent = parent

		attrs = common.node_attributes(node)


		# Create the view
		self.view = ViewChart( parent )
		self.view.title = attrs.get('string', _('Unknown') )
		self.view.model = self.parent.current_model

		if 'chart' in modules:
			widget, on_write = self.parse( self.parent.current_model, node, fields , self.view )
		else:
			widget = QLabel( _('<center><b>Could not load charts: %s</b></center>') % errors['chart'], self.view )
			on_write = None

		self.view.setWidget( widget )

		return self.view, on_write

	def parse(self, model, root_node, fields, container):
		attrs = common.node_attributes(root_node)
		self.title = attrs.get('string', 'Unknown')

		on_write = '' 

		axis = []
		axis_data = {}
		for node in root_node.childNodes:
			node_attrs = common.node_attributes(node)
			if node.localName == 'field':
				axis.append(str(node_attrs['name']))
				axis_data[str(node_attrs['name'])] = node_attrs

		#
		# TODO: parse root_node to fill in axis
		#

		try:
			_container = Chart( self.parent.current_model, axis, fields, axis_data, attrs,container)
		except Exception, e:
			common.error('Graph', _('Can not generate graph !'), details=str(e))
			_container = EmptyGraph(model, axis, fields, axis_data, attrs,container)
		return  _container, on_write


# vim:noexpandtab:

