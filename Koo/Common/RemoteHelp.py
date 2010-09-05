##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. <info@nan-tic.com>
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
import subprocess
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo import Rpc
from Koo.Common import Common
from Koo.Common import Paths


SupportAnchor = "<a href='http://www.NaN-tic.com'>NaN-tic</a>"

## @brief Opens the application used for helpdesk assistant to connect to user's desktop.
def remoteHelp(parent):
	message = _("<p><b>Remote Help</b> will allow you to share your desktop with one member "
		"of our support team. This will provide you with first class "
		"support in real time by an application expert.</p>"
		"<p>You will be able to close the connection at any time by right "
		"clicking the orange icon that will appear in the system tray of your "
		"desktop.</p>"
		"<p>In order to receive such service, you should first contract the support "
		"at %(anchor)s.</p>"
		"<p>Once you've contracted it, you can contact our helpdesk department "
		"and one member of our staff will contact you briefly and tell you which "
		"channel you have to use in the next dialog.</p>"
		"<p>If you already received the call of one member of our experts you can "
		"proceed.</p>") % {
			'anchor': SupportAnchor
		}
	answer = QMessageBox.question(parent, _('Remote Help'), message, _("Proceed"), _("Cancel") )
	if answer == 1:
		return
	language = Rpc.session.context and Rpc.session.context.get('lang') or 'en'
	if not language in ('ca','es','en'):
		language = 'en'
	
	path = os.path.join( 'Plugins', 'RemoteHelp', 'data' )
	path = Paths.searchFile( 'koo_help_%s.exe' % language, path )
	if path:
		subprocess.Popen([path])

def isRemoteHelpAvailable():
	return os.name == 'nt'
