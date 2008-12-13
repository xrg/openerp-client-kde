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

## @brief The PluggableFields class specializes in scanning for available
# widgets and delegates. 
#
# To add a new widget or delegate, simply create a new directory and put a 
# __terp__.py file that looks like this:
#
# [ 
# 	{ 'name': 'char', 'type': 'widget', 'class': 'WidgetClass' }
# ] 
# 
# Use 'delegate' for Delegates.
# Each directory can handle as many widgets and delegates as you may need.

class PluggableFields:
	imports = {}
	widgets = {}
	delegates = {}

	@staticmethod
	def scan():
		# Scan only once
		if PluggableFields.imports:
			return
		dir=os.path.abspath(os.path.dirname(__file__))
		for i in os.listdir(dir):
			path = os.path.join( dir, i, '__terp__.py' )
			if os.path.isfile( path ):
				#try:
				moduleDicts = eval( file(path).read() )
				moduleDelegates = {}
				moduleWidgets = {}
				for w in moduleDicts:
					if w['type'] == 'widget':
						moduleWidgets[ w['name'] ] = w['class']
					elif w['type'] == 'delegate':
						moduleDelegates[ w['name'] ] = w['class']
					else:
						print "Invalid type: %s" % w['type']
				PluggableFields.widgets.update( moduleWidgets )
				PluggableFields.delegates.update( moduleDelegates )
				for w in moduleDicts:
					PluggableFields.imports[ w['class'] ] = i
				#except:
					#print "Error importing widget: ", i
