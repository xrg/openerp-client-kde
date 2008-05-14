from osv import osv, fields

class res_partner_address(osv.osv):
	_name = 'res.partner.address'
	_inherit = 'res.partner.address'

	def url(self, street, zip, city, country):
		return 'http://maps.google.com/maps?q=%s %s %s %s' % ( street, zip, city, country )
		#return 'http://maps.yahoo.com/#mvt=m&zoom=17&q1=%s %s %s %s' % ( street, zip, city, country )
		#return 'http://link2.map24.com/?maptype=CGI&street0=%s&zip0=%s&city0=%s&state0=&country0=es&name0=&lid=cbecdb9d&ol=es-es' % ( street, zip, city )

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
