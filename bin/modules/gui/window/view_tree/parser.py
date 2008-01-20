##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from xml.parsers import expat

from common import common

## @brief The TreeParser class parses the arch (XML) of tree views.
#
# In order to use this function execute the parse() function with the XML
# data to parse as string.
# This will fill in the title (string), toolbar (boolean) and fieldsOrder 
# (list). 
#
# title contains the 'string' attribute set in the 'tree'
# tag of the XML or 'Tree' if none was specified. The 
# same applies to the toolbar property with the 'toolbar' attribute.
# The fieldsOrder property, is the list of field names specified in the XML
# in the exact same order that appear there.
class TreeParser:
	def tagStart(self, name, attrs):
		if name=='tree':
			self.title = attrs.get('string',_('Tree'))
			self.toolbar = bool(attrs.get('toolbar',False))
		elif name=='field':
			if 'icon' in attrs:
				self.fieldsOrder.append(str(attrs['icon']))
			self.fieldsOrder.append(str(attrs['name']))
		else:
			import logging
			log = logging.getLogger('view')
			log.error('unknown tag: '+str(name))
			del log

	## This function parses the xml data provided as parameter.
	# This function fills class member properties: title, toolbar and 
	# fieldsOrder
	def parse(self, xmlData):
		self.fieldsOrder = []

		psr = expat.ParserCreate()
		psr.StartElementHandler = self.tagStart
		psr.Parse(xmlData.encode('utf-8'))

