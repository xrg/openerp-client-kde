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

import wizard
import pooler
from osv import osv, fields

class wizard_start(osv.osv_memory):
	_name = 'fts.wizard'

	def _get_configs(self, cr, uid, context={}):
		cr.execute( "SELECT cfgname FROM pg_catalog.pg_ts_config ORDER BY cfgname" )
		result = []
		for record in cr.fetchall():
			result.append( (record[0], record[0]) )
		return result
			
	_columns = {
		'configuration': fields.selection(_get_configs, 'Configuration', method=True, required=True, help="Choose a PostgreSQL TS configuration"),
	}

	def start(self, cr, uid, ids, context={}):
		pass	
	
	def action_update_index(self, cr, uid, ids, context={}):
		# Check FTS availability
		cr.execute("SELECT 1 FROM pg_catalog.pg_type WHERE typname='tsvector'")
		if cr.rowcount == 0:
			print "It seems that TSearch2 is NOT installed"
			return {}

		# Check PL/PythonU
		cr.execute("SELECT * FROM pg_catalog.pg_language WHERE lanname='plpythonu'")
		if cr.rowcount == 0:
			cr.execute("CREATE LANGUAGE plpythonu;")

		# Set default FTS configuration
		cr.execute( "SELECT cfgname FROM pg_catalog.pg_ts_config WHERE cfgname='default'" )
		if cr.rowcount != 0:
			cr.execute('DROP TEXT SEARCH CONFIGURATION "default"')

		wizard = self.browse(cr, uid, ids, context)[0]
		cr.execute( 'CREATE TEXT SEARCH CONFIGURATION "default" (COPY=%s)' % wizard['configuration'] )

		self.recreate_core(cr)
		self.create_indexes(cr)
		cr.execute("DELETE FROM fts_current_full_text_index")
		cr.execute("INSERT INTO fts_current_full_text_index SELECT * FROM fts_full_text_index")
		return {}

	def recreate_core(self,cr):
		cr.execute("DROP TABLE IF EXISTS fts_full_text_search")
	
		cr.execute("""
			CREATE TABLE fts_full_text_search (
				message tsvector NOT NULL,
				model INT8 NOT NULL,
				reference INT8 NOT NULL,
				PRIMARY KEY ( model, reference ),
				FOREIGN KEY ( model ) REFERENCES ir_model ( id ) ON UPDATE CASCADE ON DELETE CASCADE
			) WITHOUT OIDS
			""")
		cr.execute("CREATE INDEX fts_full_text_search_idx ON fts_full_text_search USING GIST (message)")
		cr.execute("DROP FUNCTION IF EXISTS fts_full_text_search_trigger() CASCADE")
		cr.execute("""
			CREATE FUNCTION fts_full_text_search_trigger() RETURNS trigger AS
			$$
				from psycopg2.extensions import adapt as sql_quote

				if len(TD["args"]) != 2:
					plpy.error( "fts_full_text_search_trigger requires two arguments" )

				if TD["event"] == "INSERT" or TD["event"] == "UPDATE":
					tsVector = []
					for i in TD["args"][1].split(","):
						name = i.split('|')[0]
						weight = i.split('|')[1]
						value = TD["new"][name]
						if value != None:
							tsVector.append( "setweight( to_tsvector( 'default', %s::TEXT ), %s )" % (sql_quote(value).getquoted(),sql_quote(weight)) )
					if tsVector:
						tsVector = ' || '.join(tsVector)
					else:
						tsVector = "to_tsvector( 'default', '' )"

				if TD["event"] == "INSERT":
					plpy.execute( "INSERT INTO fts_full_text_search(model, reference, message) \
						VALUES (%s,%s,%s)" % (int(TD["args"][0]), int(TD["new"]["id"]), tsVector) )
				elif TD["event"] == "UPDATE":
					plpy.execute( "UPDATE fts_full_text_search SET message=%s WHERE model=%s \
						AND reference=%s" % (tsVector, int(TD["args"][0]), int(TD["old"]["id"])) )
				elif TD["event"] == "DELETE":
					plpy.execute( "DELETE FROM fts_full_text_search WHERE model=%s \
						AND reference=%s" % (int(TD["args"][0]), int(TD["old"]["id"])) )
			$$ LANGUAGE plpythonu;
			""")

	def create_indexes(self, cr):
		cr.execute("SELECT DISTINCT model_id FROM fts_full_text_index i, ir_model_fields f WHERE i.field_id=f.id");
		for j in [x[0] for x in cr.fetchall()]:
			self.create_index(cr, j)

	def create_index(sself, cr, model_id):
		cr.execute("SELECT model FROM ir_model WHERE id=%s", (model_id,) )
		tuple=cr.fetchone()
		model_name=tuple[0]

		pool = pooler.get_pool(cr.dbname)
		table_name = pool.get(model_name)._table

		cr.execute("SELECT f.name, p.name FROM fts_full_text_index i, fts_priority p, ir_model_fields f WHERE i.field_id=f.id AND i.priority=p.id AND f.model_id=%s", (model_id,) )
		tsVector = []
		fields = []
		for record in cr.fetchall():
			name = record[0]
			weight = record[1]
			tsVector.append( "setweight( to_tsvector('default', COALESCE(%s::TEXT,'')), '%s' )" % (name, weight) )
			fields.append( '%s|%s' % ( str(name), weight ) )
		tsVector = ' || '.join( tsVector )
		fields = ','.join( fields )

		if tsVector != "''":
			cr.execute("""
				DELETE FROM 
					fts_full_text_search 
				WHERE 
					model = (SELECT id FROM ir_model WHERE model=%s) 
				""", (model_name,) )
			cr.commit()
			cr.execute(
				"""
					INSERT INTO 
						fts_full_text_search(model,reference,message) 
					SELECT 
						model.id, 
						tbl.id, 
						%s
					FROM 
						\"%s\" AS tbl,
						(SELECT id FROM ir_model WHERE model='%s') AS model
				""" % (tsVector, table_name, model_name) )
			cr.commit()
			cr.execute("SELECT id FROM ir_model WHERE model=%s", (model_name,) )
			cr.execute("DROP TRIGGER IF EXISTS \"%s_fts_full_text_search\" ON \"%s\"" % (table_name, table_name ) )
			cr.commit()
			cr.execute("CREATE TRIGGER \"" + table_name + "_fts_full_text_search\" BEFORE INSERT OR UPDATE OR DELETE ON \"" + table_name + "\" FOR EACH ROW EXECUTE PROCEDURE fts_full_text_search_trigger(%s,%s)", (model_id, fields) )
			cr.commit()
	
wizard_start()
