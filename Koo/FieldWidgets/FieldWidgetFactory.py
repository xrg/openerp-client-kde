
##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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

import os

## @brief The FieldWidgetFactory class specializes in creating the appropiate 
# widgets. Searches for the available widgets and calls the parser of 
# the appropiate one.
#
# To add a new widget, simply create a new directory and put a __terp__.py file.
# The file should look like this:
# {
# 	'widgettype' : WidgetClass
# }
# Each directory could handle more than one widget types.

class FieldWidgetFactory:
	@staticmethod
	def create(widgetType, parent, view, attributes):
		# Search for all available widgets
		imports = {}
		widgets = {}
		dir=os.path.abspath(os.path.dirname(__file__))
		for i in os.listdir(dir):
			path = os.path.join( dir, i, '__terp__.py' )
			if os.path.isfile( path ):
				try:
					moduleWidgets = eval( file(path).read() )
					widgets.update(moduleWidgets)
					for key in moduleWidgets:
						imports[key] = i
				except:
					print "Error importing widget: ", i

		if not widgetType in imports:
			print "Widget '%s' not available" % widgetType
			return None

		exec( 'import %s' % imports[widgetType] )
		return eval( '%s(parent, view, attributes)' % widgets[widgetType] )

