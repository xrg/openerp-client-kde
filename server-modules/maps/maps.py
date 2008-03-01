from osv import osv, fields

class res_partner_address(osv.osv):
	_name = 'res.partner.address'
	_inherit = 'res.partner.address'

	def url(self, street, zip, city, country):
		return 'http://maps.google.com/maps?q=%s %s %s %s' % ( street, zip, city, country )

	def _partner_address_map(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for p in self.browse(cr, uid, ids, context):
			street = p.street or ''
			zip = p.zip or ''
			city = p.city or ''
			if p.country_id:
				country = p.country_id.name
			else:
				country = ''
			res[p.id] = self.url( street, zip, city, country )
		return res

	_columns = {
		'map': fields.function(_partner_address_map, method=True, type='char', size=1024, string='Map'),
	}

	def onchange_map(self, cr, uid, ids, street, zip, city, country_id):
		street=street or ''
		zip=zip or ''
		city=city or ''
		#print country_id
		country = ''
		if country_id:
			c = self.pool.get('res.country').read(cr, uid, [country_id])
			if c:
				country = c[0]['name']
		v = { 'map' : self.url(street, zip, city, country) }
		return { 'value' : v }

res_partner_address()
