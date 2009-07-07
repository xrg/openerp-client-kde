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

{
	"name" : "Pyro",
	"version" : "0.1",
	"description" : """This module adds new protocol to OpenERP server.

In order to use the pyro (PYROLOC://) protocol you must install this module. Once installed try to log in again using Koo and choose the same server but with port 8071 and protocol Pyro.

Note that if you restart the server you'll need to ensure the module is started. That can be done in two different ways. Either you start the server using "-d database_name" option or you log in using another protocol first.

This module needs pyro from http://sourceforge.net/projects/pyro/files/ on client and server.
""",
	"author" : "NaN",
	"website" : "http://www.nan-tic.com",
	"depends" : ["base"],
	"category" : "Generic Modules/Pyro",
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [],
	"active": False,
	"installable": True
}

