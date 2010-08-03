##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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
import sys

## @brief This functions searches the given file (optionally adding a subdirectory)
# in the possible directories it could be found.
#
# This should hide different installation and operating system directories. Making
# it easier to find resource files.
def searchFile(file, subdir=None):
	tests = []
	if subdir:
		tests += [os.path.join( x, subdir ) for x in sys.path]
		tests += [os.path.join( x, 'Koo', subdir ) for x in sys.path]
		# The following line is needed for Koo to work properly
		# under windows. Mainly we say attach 'share/koo/subdir' to
		# sys.path, which by default has 'c:\python25' (among others). 
		# This will give 'c:\python25\share\koo\ui' for example, which is 
		# where '.ui' files are stored under the Windows platform.
		tests += [os.path.join( x, 'share', 'Koo', subdir ) for x in sys.path]
		tests += ['%s/share/Koo/%s' % ( sys.prefix, subdir)]
	else:
		tests += [os.path.join( x, 'Koo' ) for x in sys.path]
		tests += sys.path

	for p in tests:
		x = os.path.join(p, file)
		if os.path.exists(x):
			return x
	# Previously we returned False but None is more appropiate
	# and even some functions (such as initializeTranslations using
	# gettext.translation() will depend on it).
	return None

uiPath = lambda x: searchFile(x, 'ui')

