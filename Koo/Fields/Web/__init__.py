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

from Common import Debug

from WebFieldWidget import *
from Koo.Fields.FieldWidgetFactory import *

try:
	from PyQt4.QtWebKit import *
	from PyQt4.QtNetwork import *

	FieldWidgetFactory.register( 'web', WebFieldWidget )

except:
	Debug.warning(_('QtWebKit or QtNetwork not found. Web field will not be available.'))

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
