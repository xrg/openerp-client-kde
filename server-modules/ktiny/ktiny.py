from osv import osv, fields

class ir_attachment(osv.osv):
	_name = 'ir.attachment'
	_inherit = 'ir.attachment'
	_columns = {
		'res_model': fields.char('Resource Model', size=64, readonly=False),
		'res_id': fields.integer('Resource ID', readonly=False),
	}
ir_attachment()

class res_roles(osv.osv):
	_name = 'res.roles'
	_inherit = 'res.roles'
	_columns = {
		'ktiny_settings_id': fields.many2many('nan.ktiny.settings', 'nan_ktiny_settings_roles_rel', 'role_id', 'setting_id', 'KTiny Settings')
	}

class nan_ktiny_settings(osv.osv):
	_name = 'nan.ktiny.settings'

	_columns = {
		'name': fields.char( 'Settings Name', 50, required=True ),
		'show_toolbar': fields.boolean( 'Show toolbar' ),
		'tabs_position': fields.selection( [('left', 'Left'), ('top', 'Top'), 
			('right', 'Right'), ('bottom', 'Bottom')], 'Default tabs position' ),
		'stylesheet': fields.text( 'Stylesheet' ),
		'sort_mode': fields.selection( [('visible_items', 'Visible Items'), ('all_items', 'All Items')], 'Sorting Mode' ),
		'limit': fields.integer('Limit'),
		'requests_refresh_interval': fields.integer('Requests refresh interval (seconds)'),
		'show_system_tray_icon': fields.boolean( 'Show Icon in System Tray' ),
		'roles_id': fields.many2many('res.roles', 'nan_ktiny_settings_roles_rel', 'setting_id', 'role_id', 'Roles')
	}

	# Returns the id of the settings to load. Currently only uses roles to
	# decide the appropiate settings, but in the future it could use user IP
	# address or other supplied parameters.
	def get_settings_id(self, cr, uid):
		user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
		ids = [x.id for x in user.roles_id]
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

#class nan_ktiny_session(osv.osv):
	#_name = 'nan.ktiny.session'
#
	#_columns = {
		#
	#}
#nan_ktiny_session()
#
#class nan_ktiny_list_view(osv.osv):
	#_name = 'nan.ktiny.list_view'	
	#_columns = {
	#}
#nan_ktiny_list_view()
