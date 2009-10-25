##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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

from SvgView import SvgView
from Koo.View.AbstractParser import *
from Koo.Fields.FieldWidgetFactory import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Common import Common

import os


class SvgParser(AbstractParser):

	def create(self, viewId, parent, viewModel, rootNode, fields, filter=None):
		self.viewModel = viewModel
		self.filter = filter
		self.widgetList = []
		# Create the view
		self.view = SvgView( parent )
		self.view.id = viewId
		self.view
		directory = os.path.abspath(os.path.dirname(__file__))

		for node in rootNode.childNodes:
			if node.localName == 'field':
				attributes = Common.nodeAttributes(node)
				name = attributes['name']
				type = attributes.get('widget', fields[name]['type'])
				fields[name].update(attributes)
				fields[name]['model'] = viewModel

				# Create the appropiate widget for the given field type
				widget = FieldWidgetFactory.create( type, None, self.view, fields[name] )
				if not widget:
					continue
				self.view.widgets[name] = widget

		self.view.fields = fields

		self.view.setSvg( os.path.join( directory, 'restaurant.svg' ) )
		return self.view


# vim:noexpandtab:
