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

	_columns = {
		'name': fields.char( 'Settings Name', 50, required=True ),
		'show_toolbar': fields.boolean( 'Show toolbar' ),
		'tabs_position': fields.selection( [('left', 'Left'), ('top', 'Top'), 
			('right', 'Right'), ('bottom', 'Bottom')], 'Default tabs position' ),
		'stylesheet': fields.text( 'Stylesheet' )
	}

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
