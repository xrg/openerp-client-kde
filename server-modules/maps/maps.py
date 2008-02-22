from osv import osv, fields

class res_partner_address(osv.osv):
	_name = 'res.partner.address'
	_inherit = 'res.partner.address'
	_columns = {
		'map': fields.char('Map', size=1024, readonly=True)
	}

	def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
		if 'map' in fields:
			if not 'city' in fields:
				fields.append('city')
			if not 'street' in fields:
				fields.append('street')
			if not 'zip' in fields:
				fields.append('zip')
			if not 'country_id' in fields:
				fields.append('country_id')
		res = super(res_partner_address, self).read(cr, uid, ids, fields, context, load)
		
		if 'map' in fields:
			for x in res:
				street=x['street'] or ''
				zip=x['zip'] or ''
				city=x['city'] or ''
				if x['country_id']:
					country=x['country_id'][1]
				else:
					country=''
				x['map'] = self.url( street, zip, city, country )
		return res

	def url(self, street, zip, city, country):
		return 'http://maps.google.com/maps?q=%s %s %s %s' % ( street, zip, city, country )

	def onchange_map(self, cr, uid, ids, street, zip, city, country_id):
		street=street or ''
		zip=zip or ''
		city=city or ''
		print country_id
		country = ''
		if country_id:
			c = self.pool.get('res.country').read(cr, uid, [country_id])
			if c:
				country = c[0]['name']
		v = { 'map' : self.url(street, zip, city, country) }
		return { 'value' : v }

res_partner_address()
