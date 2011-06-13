# encoding: iso-8859-15
import wizard
import pooler
import base64
import osv
from tools.translate import _

view_form_start = """<?xml version="1.0"?>
	<form string="Create Data Template">
		<group colspan="2">
			<field name="model"/>
			<field name="depth"/>
		</group>
	</form>"""

view_fields_start = {
	'model': { 'string': 'Model', 'type': 'many2one', 'relation': 'ir.model', 'required': True },
	'depth': { 'string':'Depth', 'type':'integer', 'required': True },
}

view_form_end = """<?xml version="1.0"?>
	<form string="Create Data Template">
		<group colspan="2">
			<field name="model"/>
			<field name="data" filename="filename"/>
			<field name="filename" invisible="1"/>
		</group>
	</form>"""

view_fields_end = {
	'model': { 'string': 'Model', 'type': 'char', 'readonly': True },
	'data': { 'string': 'XML', 'type': 'binary', 'relation': 'ir.model', 'readonly': True },
	'filename': { 'string': 'File Name', 'type': 'char' },
}

class create_data_template(wizard.interface):
	
	def _action_start(self, cr, uid, data, context):
		res = {
			'depth': 1
		}
		return res

	def _action_create_xml(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		form = data['form']
		values = pool.get('ir.model').read(cr, uid, form['model'], ['name','model'], context)
		name = values['name']
		model = values['model']

		
		xml = pool.get('ir.actions.report.xml').create_xml(cr, uid, model, form['depth'], context)

		return {
			'model': name,
			'data': base64.encodestring( xml ),
			'filename': 'jasper.xml',
		}

	states = {
		'init': {
			'actions': [_action_start],
			'result': {
				'type': 'form', 
				'arch': view_form_start, 
				'fields': view_fields_start, 
				'state': [('end','Cancel','gtk-cancel'),('create','Create','gtk-ok')]
			}
		},
		'create': {
			'actions': [_action_create_xml],
			'result': {
				'type': 'form', 
				'arch': view_form_end, 
				'fields': view_fields_end, 
				'state': [('end','Accept','gtk-ok')]
			}
		}
	}

create_data_template('jasper_create_data_template')
