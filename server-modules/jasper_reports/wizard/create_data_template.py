from xml.dom.minidom import getDOMImplementation
import wizard
import pooler
import base64
import osv

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
			<field name="data"/>
		</group>
	</form>"""

view_fields_end = {
	'model': { 'string': 'Model', 'type': 'char', 'readonly': True },
	'data': { 'string': 'XML', 'type': 'binary', 'relation': 'ir.model', 'readonly': True }
}


class create_data_template(wizard.interface):
	
	def _action_start(self, cr, uid, data, context):
		res = {
			'depth': 1
		}
		return res
		
	def generate_xml(self, pool, name, parentNode, document, depth):
		model = pool.get(name)
		fields = model._columns.keys()
		fields.sort()
		for field in fields:
			fieldNode = document.createElement(field)
			parentNode.appendChild( fieldNode )
			type = model._columns[field]._type
			if type in ('many2one','one2many','many2many'):
				if depth <= 1:
					continue
				newName = model._columns[field]._obj
				self.generate_xml(pool, newName, fieldNode, document, depth-1)
				continue
			
			if type == 'float':
				value = '12345.67'
			elif type == 'integer':
				value = '12345'
			elif type == 'date':
				value = '2009-12-31 00:00:00'
			elif type == 'time':
				value = '12:34:56'
			elif type == 'datetime':
				value = '2009-12-31 12:34:56'
			else:
				value = field

			valueNode = document.createTextNode( value )
			fieldNode.appendChild( valueNode )

		if depth > 1 and name != 'Attachments':
			# Create relation with attachments
			fieldNode = document.createElement( 'Attachments' )
			parentNode.appendChild( fieldNode )
			self.generate_xml(pool, 'ir.attachment', fieldNode, document, depth-1)

	def _action_create_xml(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		form = data['form']
		values = pool.get('ir.model').read(cr, uid, form['model'], ['name','model'])
		name = values['name']
		model = values['model']

		document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = document.documentElement
		recordNode = document.createElement('record')
		topNode.appendChild( recordNode )
		self.generate_xml( pool, model, recordNode, document, form['depth'] )
		topNode.toxml()

		res = {
			'model': name,
			'data': base64.encodestring( topNode.toxml() )
		}
		return res

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
