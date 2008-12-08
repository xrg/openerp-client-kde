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

from osv import osv, fields

class ir_attachment(osv.osv):
	_name = 'ir.attachment'
	_inherit = 'ir.attachment'
	_columns = {
		'res_model': fields.char('Resource Model', size=64, readonly=False),
		'res_id': fields.integer('Resource ID', readonly=False),
	}
ir_attachment()

class nan_ktiny_settings(osv.osv):
	_name = 'nan.ktiny.settings'

	def _check_limit(self, cr, uid, ids, context={}):
		for x in self.read(cr, uid, ids, ['limit']):
			if x['limit'] <= 0:
				return False
		return True

	def _check_interval(self, cr, uid, ids, context={}):
		for x in self.read(cr, uid, ids, ['requests_refresh_interval']):
			if x['requests_refresh_interval'] <= 0:
				return False
		return True

	_columns = {
		'name': fields.char( 'Settings Name', 50, required=True, help='Name to be given to these settings.' ),
		'show_toolbar': fields.boolean( 'Show toolbar', help='Whether toolbar is shown on screens. Note the toolbar may be convenient but not necessary as all options are available from the Reports, Actions, Browse and Plugins menu entries.' ),
		'tabs_position': fields.selection( [('left', 'Left'), ('top', 'Top'), 
			('right', 'Right'), ('bottom', 'Bottom')], 'Default tabs position', help='Tabs can be on the left, top, right or bottom by default. Note that some screens may require an specific position which will override this default.' ),
		'stylesheet': fields.text( 'Stylesheet', help='A valid Qt Stylesheet can be provided to be applied once the user has logged in.' ),
		'sort_mode': fields.selection( [('visible_items', 'Visible Items'), ('all_items', 'All Items')], 'Sorting Mode', help='If set to "Visible Items" only the "Limit" elements are loaded and sorting is done in the client side. If "All Items" is used, sorting is done in the server and all records are (virtually) loaded in chunks of size "Limit"'),
		'limit': fields.integer('Limit',help='Number of records to be fetched at once.'),
		'requests_refresh_interval': fields.integer('Requests refresh interval (seconds)', help='Indicates the number of seconds to wait to check if new requests have been received by the current user.'),
		'show_system_tray_icon': fields.boolean( 'Show Icon in System Tray', help='If checked, an icon is shown in the system tray to keep Koo accessible all the time.' ),
		'roles_id': fields.many2many('res.roles', 'nan_ktiny_settings_roles_rel', 'setting_id', 'role_id', 'Roles', help='Roles to which these settings apply.'),
		'print_directly': fields.boolean( 'Print directly', help='If set, sends the document directly to the printer. Otherwise the document is shown in a PDF viewer.' )
	}
	_defaults = {
		'limit': lambda *a: 80,
		'requests_refresh_interval': lambda *a: 300,
	}
	_constraints = [
		(_check_limit, 'Limit must be greater than zero.', ['limit']),
		(_check_interval, 'Requests refresh interval must be greater than zero.', ['requests_refresh_interval']),
	]
	

	# Returns the id of the settings to load. Currently only uses roles to
	# decide the appropiate settings, but in the future it could use user IP
	# address or other supplied parameters.
	def get_settings_id(self, cr, uid):
		user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
		ids = [x.id for x in user.roles_id]
		if not ids:
			return False
		ids = str(ids).replace('[', '(').replace(']',')')
		cr.execute( "SELECT setting_id FROM nan_ktiny_settings_roles_rel WHERE role_id IN %s" % ( ids ) )
		row = cr.fetchone()
		if row:
			return row[0]
		else:
			return False

	def get_settings(self, cr, uid):
		id = self.get_settings_id(cr, uid)
		if not id:
			return {}
		return self.read(cr, uid, [id])
		
nan_ktiny_settings()

class nan_ktiny_view_settings(osv.osv):
	_name = 'nan.ktiny.view.settings'
	_columns = {
		'user': fields.many2one('res.users', 'User'),
		'view': fields.many2one('ir.ui.view', 'View'),
		'data': fields.text('Data')
	}
nan_ktiny_view_settings()

