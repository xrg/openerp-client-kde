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

view_form_end = """<?xml version="1.0"?>
	<form string="Full text index update done">
		<separator string="System upgrade done"/>
		<label align="0.0" string="The full text index has been updated!" colspan="4"/>
	</form>"""

view_form = """<?xml version="1.0"?>
	<form string="Full text index update">
		<image name="gtk-info" size="64" colspan="2"/>
		<group colspan="2" col="4">
			<label align="0.0" string="The full text index will be updated." colspan="4"/>
			<label align="0.0" string="Note that this operation may take a lot of time, depending on the amount of new indexes and the number of records in the database." colspan="4"/>
			<separator string="Indexes to update"/>
		</group>
	</form>"""

view_field = {
	"module_info": {'type':'text', 'string':'Modules', 'readonly':True}
}


class wizard_info_get(wizard.interface):
	def _get_install(self, cr, uid, data, context):
		return {}
#return {'module_info':'List of modules...'}
	
	def _update_index(self, cr, uid, data, context):
		cr.execute("SELECT 1 FROM pg_catalog.pg_type WHERE typname='tsvector'")
		if cr.rowcount == 0:
			print "It seems that TSearch2 is NOT installed"
			return {}
		self.recreate_core(cr)
		#self.remove_indexes(cr)
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
						value = TD["new"][i]
						if value != None:
							tsVector.append( "to_tsvector( 'default', %s )" % sql_quote(value).getquoted() )
					tsVector = ' || '.join(tsVector)

				if TD["event"] == "INSERT":
					plpy.execute( "INSERT INTO fts_full_text_search(model, reference, message) \
						VALUES (%d,%d,%s)" % (int(TD["args"][0]), int(TD["new"]["id"]), tsVector) )
				elif TD["event"] == "UPDATE":
					plpy.execute( "UPDATE fts_full_text_search SET message=%s WHERE model=%d \
						AND reference=%d" % (tsVector, int(TD["args"][0]), int(TD["old"]["id"])) )
				elif TD["event"] == "DELETE":
					plpy.execute( "DELETE FROM fts_full_text_search WHERE model=%d \
						AND reference=%d" % (int(TD["args"][0]), int(TD["old"]["id"])) )
			$$ LANGUAGE plpythonu;
			""")

	# As it's not trivial and I don't have much time ATM I will
	# make it very unoptimal and remove all indexes and triggers
	# and recreate the necessary ones. This means that no use of 
	# the previous indexes is taken into account.
	def remove_indexes(self, cr):
		pool = pooler.get_pool(cr.dbname)

		# Remove all triggers
		cr.execute("SELECT DISTINCT f.model AS t FROM fts_current_full_text_index i, ir_model_fields f WHERE i.field_id= f.id")
		for i in [x[0] for x in cr.fetchall()]:
			table_name = pool.get(i)._table
			cr.execute("DROP TRIGGER \"%s_fts_full_text_search\" ON \"%s\"" % (table_name, table_name) )

		# Remove indexed information
		cr.execute("DELETE FROM fts_full_text_search")
		return

	def create_indexes(self, cr):
		cr.execute("SELECT DISTINCT model_id FROM fts_full_text_index i, ir_model_fields f WHERE i.field_id=f.id");
		for j in [x[0] for x in cr.fetchall()]:
			self.create_index(cr, j)

	def create_index(sself, cr, model_id):
		cr.execute("SELECT model FROM ir_model WHERE id=%d", (model_id,) )
		tuple=cr.fetchone()
		model_name=tuple[0]

		pool = pooler.get_pool(cr.dbname)
		table_name = pool.get(model_name)._table

		cr.execute("SELECT f.name FROM fts_full_text_index i, ir_model_fields f WHERE i.field_id=f.id AND f.model_id=%d", (model_id,) )
		tsVector = []
		fields = []
		for k in [x[0] for x in cr.fetchall()]:
			tsVector.append( "COALESCE(to_tsvector('default', %s), to_tsvector('default',''))" % k )
			fields.append( str(k) )
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
			cr.execute("CREATE TRIGGER \"" + table_name + "_fts_full_text_search\" BEFORE INSERT OR UPDATE OR DELETE ON \"" + table_name + "\" FOR EACH ROW EXECUTE PROCEDURE fts_full_text_search_trigger(%d,%s)", (model_id, fields) )
			cr.commit()
	
	states = {
		'init': {
			'actions': [_get_install],
			'result': {'type':'form', 'arch':view_form, 'fields':{}, 'state':[('end','Cancel','gtk-cancel'),('start','Start Update','gtk-ok')]}
		},
		'start': {
			'actions': [_update_index],
			'result': {'type':'form', 'arch':view_form_end, 'fields': {}, 'state':[('end','Close','gtk-close')]}
		}
	}
wizard_info_get('index_update')
