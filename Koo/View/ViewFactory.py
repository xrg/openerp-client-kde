##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import os

# The 'ViewFactory' class specializes in creating the appropiate views. Searches
# for available views and calls the parser of the appropiate one.
#
# To add a new view, simply create a new directory and put a __terp__.py file.
# The file should look like this:
# {
# 	'viewname' : ParserClass
# }
# Each directory could handle more than one view types.
# Standard types are 'form', 'tree' and 'graph'. 

class ViewFactory:
	@staticmethod
	def create(parent, model, root_node, fields):
		# Search for all available views
		parsers = {}
		imports = {}
		dir=os.path.abspath(os.path.dirname(__file__))
		for i in os.listdir(dir):
			path = os.path.join( dir, i, '__terp__.py' )
			if os.path.isfile( path ):
				try:
					x = eval( file(path).read() )
					parsers.update(x)
					imports[x.keys()[0]] = i
				except:
					print "Error importing view: ", i

		# Search for the views and parse the XML 
		widget = None
		for node in root_node.childNodes:
			if not node.nodeType == node.ELEMENT_NODE:
				continue
			if node.localName in parsers:
				exec( 'import %s' % imports[node.localName] )	
				parser = eval('%s()' % parsers[node.localName])
				view, on_write = parser.create(parent, model, node, fields)
				return view, on_write
		return None

