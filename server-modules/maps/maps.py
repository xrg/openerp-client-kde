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

class res_partner_address(osv.osv):
	_name = 'res.partner.address'
	_inherit = 'res.partner.address'

	def url(self, street, zip, city, country):
		#return 'http://maps.google.com/maps?q=%s %s %s %s' % ( street, zip, city, country )
		return 'http://maps.yahoo.com/#mvt=m&zoom=17&q1=%s %s %s %s' % ( street, zip, city, country )
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
