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

from service import security
from osv.orm import except_orm
import netsvc
import sql_db
import pooler
from psycopg2.extensions import adapt as sql_quote
import SimpleXMLRPCServer
from operator import itemgetter


def quote(value):
	return sql_quote(value.encode('latin1')).getquoted()

def isInteger(value):
	try:
		long(value)
		return True
	except ValueError, e:
		return False

def isFloat(value):
	try:
		float(value)
		return True
	except ValueError, e:
		return False

def noneToFalse(value):
	if type(value)==type([]):
		return map(noneToFalse, value)
	elif type(value)==type(()):
		return map(noneToFalse, value)
	elif type(value)==type({}):
		newval = {}
		for i in value.keys():
			newval[i] = noneToFalse(value[i])
		return newval 
	elif value == None:
		return False
	else:
		return value 


class fulltextsearch_services(netsvc.Service):
	def __init__(self, name="fulltextsearch"):
		netsvc.Service.__init__(self,name)
		self.joinGroup('web-services')
		self.exportMethod(self.search)
		self.exportMethod(self.indexedModels)
		self.postgresVersion = None
		self.hasIntegratedTs = False
		self.postgresKeyWords = {}
		
	# This method should not be exported
	def checkPostgresVersion(self, cr):
		if not self.postgresVersion:
			cr.execute("SELECT version();")
			version = cr.fetchone()[0]
			# The next line should obtain version number, something like '8.3'.
			self.postgresVersion = version.split(' ')[1]
			version = self.postgresVersion.split('.')
			major = version[0]
			minor = version[1]
			if major > '8' or (major == '8' and minor >= '3'):
				self.hasIntegratedTs = True
			else:
				self.hasIntegratedTs = False
		
			if self.hasIntegratedTs:
				self.postgresKeyWords[ 'ts_rank' ] = 'ts_rank'
				self.postgresKeyWords[ 'ts_headline' ] = 'ts_headline'
			else:
				self.postgresKeyWords[ 'ts_rank' ] = 'rank'
				self.postgresKeyWords[ 'ts_headline' ] = 'headline'

	# This method should not be exported
	def headline( self, cr, pool, text, id, model_id, model_name ):
		# Get all the fields of the model that are indexed
		cr.execute( """
			SELECT
				f.name
			FROM
				fts_current_full_text_index i,
				ir_model_fields f
			WHERE
				i.field_id = f.id AND
				f.model_id=%d
			""", (model_id,) )
		# We will concatenate all those fields just like the
		# index does, so we can have the headline
		table = pool.get(model_name)._table
		fields = []
		for c in cr.fetchall():
			fields.append( c[0] )
		textFields = "''"
		for k in fields:
			textFields = textFields + " || ' ' || COALESCE(" + k + "::TEXT,'')"

		# Look if the model has the 'name' field. Which is the
		# 'default' field we show to represent it on screen instead
		# of the 'id'
		cr.execute( """
			SELECT
				f.name
			FROM
				ir_model_fields f
			WHERE
				f.name = 'name' AND
				f.model_id=%d 
			LIMIT 1
			""", (model_id,) )
		if cr.fetchone():
			# If it has, fetch the name of the object 
			cr.execute( "SELECT name FROM \"" + table + "\" WHERE id = %d", (id,) )
			name = cr.fetchone()[0]
		else:
			name = ""

		# Finally, obtain the headline with the concatenation of the
		# indexed fields
		cr.execute( """
			SELECT
				""" + self.postgresKeyWords['ts_headline'] + """ ( 'default', """ + textFields + """, to_tsquery('default', %s) ) 
			FROM 
				\"""" + table + """\"
			WHERE
				id = %d
			""", (text, id) )	

		return { 'name': name, 'headline': cr.fetchone()[0] }

	# Returns a list with the models that have any fields 
	# indexed with full text index.
	def indexedModels(self, db, uid, passwd, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()

		self.checkPostgresVersion(cr)

		cr.execute("""
			SELECT DISTINCT
				m.id, 
				m.name,
				m.model
			FROM 
				fts_current_full_text_index fti, 
				ir_model_fields f, 
				ir_model m 
			WHERE 
				fti.field_id = f.id AND 
				f.model_id=m.id;
			""")

		if 'lang' in context:
			lang = context['lang']
		else:
			lang = 'en_US'

		pool = pooler.get_pool(db)
		ret = []
		for x in cr.fetchall():
			# Check security permissions
			# Don't put the model in the list of indexed models
			# if the user doesn't have access to it
			try:
				pool.get('ir.model.access').check(cr, uid, x[2], 'read')
			except except_orm, e:
				continue

			# Search for the translation of the model
			name = pool.get('ir.translation')._get_source(cr, uid, 'ir.model,name', 'model', lang, x[1])
			if not name:
				name = x[1]

			ret.append( { 'id': x[0], 'name': name } )		
		ret.sort( key=itemgetter('name') )
		return ret
		
	# Searches limit records that match the text query in the specified model 
	# starting at offset.
	# If model is None or False all models are searched. Model should be the
	# identifier of the model.
	def search(self, db, uid, passwd, text, limit, offset, model, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()

		self.checkPostgresVersion(cr)

		# If text is empty return nothing. Trying to continue makes PostgreSQL
		# complain because GIN indexes don't support search with void query
		# Note that this doesn't avoid the problem when you query for a word which
		# is descarted by the TSearch2 dictionary. Such as 'a' in English.
		if text.strip() == '':
			return []

		# Parse text query so we convert dates into SQL dates (::DATE) and other 
		# types if necessary too.
		tsQuery = []
		tsVector = []
		for x in text.split(' '):
			if isFloat(x):
				tsVector.append( "to_tsvector( 'default', %f::TEXT )" % float(x) )
				tsQuery.append( "to_tsquery( 'default', %f::TEXT )" % float(x) )
			elif isInteger(x):
				tsVector.append( "to_tsvector( 'default', %d::TEXT )" % long(x) )
				tsQuery.append( "to_tsquery( 'default', %d::TEXT )" % long(x) )
			#elif isDate(x):
				#tsVector.append( "to_tsvector( 'default', %s::DATE )" % quote(date(x) )  
				#tsQuery.append( "to_tsquery( 'default', %s::DATE )" % quote(date(x) )  
			else:
				tsVector.append( "to_tsvector( 'default', %s::TEXT )" % quote(x) )
				tsQuery.append( "to_tsquery( 'default', %s::TEXT )" % quote(x) )
		tsVector = ' || '.join(tsVector)
		tsQuery = ' && '.join(tsQuery)

		if model:
			filterModel = ' AND m.id = %d ' % int(model)
		else:
			filterModel = ''

		# Note on limit & offset: Given that we might restrict some models due
		# to the user not having permissions to access them we can't use PostgreSQL
		# LIMIT & OFFSET in the query. That would be possible only if 
		# 'ir.model.access' had a function which returned a list with all the models
		# the user has access to.
		#
		# We may consider using LIMIT in the future and making multiple queries if
		# we think it can bring a performance gain, but OFFSET specified by the user 
		# can never be used in the query directly.
		try:
			cr.execute("""
				SELECT
					fts.model,
					fts.reference,
					m.name,
					m.model,
					to_char(%s(message, %s)*100, '990D99') AS ranking
				FROM
					fts_full_text_search fts,
					ir_model m
				WHERE
					m.id = fts.model AND
					message @@ %s 
					%s
				ORDER BY
					ranking DESC,
					fts.model,
					fts.reference""" % (self.postgresKeyWords['ts_rank'], tsQuery, tsQuery, filterModel) )
		except:
			return []

		if 'lang' in context:
			lang = context['lang']
		else:
			lang = 'en_US'

		pool = pooler.get_pool(db)
		ret = []
		i = -1
		all = cr.fetchall()
		for x in all:
			i = i + 1
			if i < offset:
				continue
			if i >= offset + limit:
				break
			
			model_id = x[0]
			id = x[1]
			model_label = x[2]
			model_name = x[3]
			ranking = x[4]

			# Search for the translation of the model
			model_label = pool.get('ir.translation')._get_source(cr, uid, 'ir.model,name', 'model', lang, model_label)
			if not model_label:
				model_label = x[2]


			# Check security permissions
			# If the user doesn't have access for this model we discard
			# this item.
			try:
				pool.get('ir.model.access').check(cr, uid, model_name, 'read')
			except except_orm, e:
				continue

			d = self.headline( cr, pool, text, id, model_id, model_name )
			d['id'] = id
			d['ranking'] = ranking
			d['model_id'] = model_id
			d['model_label'] = model_label
			d['model_name'] = model_name
			ret.append( d )

		return noneToFalse( ret )

fulltextsearch_services()
paths = list(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths) + ['/xmlrpc/fulltextsearch' ]
SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths = tuple(paths)


# vim:noexpandtab

