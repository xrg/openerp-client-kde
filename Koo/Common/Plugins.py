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
import sys

## @brief This helper function searches all available modules in a given directory.
# It's used to scan the Plugins, Fields, View and Search directories.
def scan( module, directory ):
	pluginImports = __import__(module, globals(), locals())
	# Check if it's being run using py2exe or py2app environment
	frozen = getattr(sys, 'frozen', None)
	if frozen == 'macosx_app' or hasattr(pluginImports, '__loader__'):
		# If it's run using py2exe or py2app environment, all files will be in a single 
		# zip file and we can't use listdir() to find all available plugins.
		zipFiles = pluginImports.__loader__._files
		moduleDir = os.sep.join( module.split('.') )
		files = [zipFiles[file][0] for file in zipFiles.keys() if moduleDir in file]
		files = [file for file in files if '__init__.py' in file]
		for file in files:
			d = os.path.dirname(file)
			if d.endswith( moduleDir ):
				continue
			newModule = os.path.basename(os.path.dirname(file))
			__import__( '%s.%s' % (module, newModule), globals(), locals(), [newModule] ) 
	else:
		for i in os.listdir(directory):
			path = os.path.join( directory, i, '__init__.py' )
			if os.path.isfile( path ):
				__import__( '%s.%s' % (module, i), globals(), locals(), [i] )

