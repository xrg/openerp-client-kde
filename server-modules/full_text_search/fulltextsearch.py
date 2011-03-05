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
    return unicode( sql_quote(value.encode('utf-8')).getquoted(), 'utf-8' )

def isInteger(value):
    try:
        long(value)
        return True
    except ValueError, e:
        return False

def isFloat(value):
    # We'll always consider 'nan' as string and thus
    # not a valid float value.
    if value.strip().lower() == 'nan':
        return False
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
                self.postgresKeyWords[ 'ts_rank' ] = u'ts_rank'
                self.postgresKeyWords[ 'ts_headline' ] = u'ts_headline'
            else:
                self.postgresKeyWords[ 'ts_rank' ] = u'rank'
                self.postgresKeyWords[ 'ts_headline' ] = u'headline'

    # This method should not be exported
    def headline( self, pool, cr, uid, text, id, model_id, model_name, context ):
        # Get all the fields of the model that are indexed
        cr.execute( """
            SELECT
                f.name
            FROM
                fts_current_full_text_index i,
                ir_model_fields f
            WHERE
                i.field_id = f.id AND
                f.model_id=%s
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

        try:
            name = pool.get( model_name ).name_get( cr, uid, [id], context )[0][1]
        except:
            name = ""

        # Finally, obtain the headline with the concatenation of the
        # indexed fields
        cr.execute( """
            SELECT
                """ + self.postgresKeyWords['ts_headline'] + """ ( 'default', """ + textFields + """, to_tsquery('default', %s) ),
                """ + self.postgresKeyWords['ts_headline'] + """ ( 'default', %s, to_tsquery('default', %s) )

            FROM
                \"""" + table + """\"
            WHERE
                id = %s
            """, (text, name, text, id) )
        record = cr.fetchone()
        return { 'name': record[1], 'headline': record[0] }

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
        cr.close()
        return ret

    # Searches limit records that match the text query in the specified model
    # starting at offset.
    # If model is None or False all models are searched. Model should be the
    # identifier of the model.
    def search(self, db, uid, passwd, text, limit, offset, model, context=None):
        if context is None:
            context = {}

        security.check(db, uid, passwd)
        pool = pooler.get_pool(db)
        conn = sql_db.db_connect(db)
        cr = conn.cursor()
        try:
            return self.search_internal(pool, cr, uid, text, limit, offset, model, context)
        except Exception, e:
            print "EX: ", str(e)
        finally:
            cr.close()

    def search_internal(self, pool, cr, uid, text, limit, offset, model, context=None):

        self.checkPostgresVersion(cr)

        if isinstance( text, str ):
            text = unicode( text, 'utf-8', 'ignore' )
        elif not isinstance( text, unicode ):
            text = unicode( text )

        # If text is empty return nothing. Trying to continue makes PostgreSQL
        # complain because GIN indexes don't support search with void query
        # Note that this doesn't avoid the problem when you query for a word which
        # is descarted by the TSearch2 dictionary. Such as 'a' in English.
        if text.strip() == '':
            return []

        # Parse text query so we convert dates into SQL dates (::DATE) and other
        # types if necessary too.
        tsQuery = []
        for x in text.split(u' '):
            if isFloat(x):
                tsQuery.append( u"to_tsquery( 'default', %s::TEXT )" % float(x) )
            elif isInteger(x):
                tsQuery.append( u"to_tsquery( 'default', %s::TEXT )" % long(x) )
            else:
                tsQuery.append( u"to_tsquery( 'default', %s::TEXT )" % quote(x) )
        tsQuery = u' && '.join(tsQuery)

        if model:
            filterModel = u' AND m.id = %s ' % int(model)
        else:
            filterModel = u''

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
            cr.execute( u"""
                SELECT
                    fts.model,
                    fts.reference,
                    m.name,
                    m.model,
                    %s(message, %s)*100 AS ranking
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

        ret = []
        i = -1
        all = cr.fetchall()
        for x in all:
            model_id = x[0]
            id = x[1]
            model_label = x[2]
            model_name = x[3]
            ranking = x[4]

            # Check security permissions using search
            try:
                if not pool.get(model_name).search(cr, uid, [('id','=',id)], context=context):
                    continue
            except except_orm, e:
                continue
            # Check read permissions using because 'search' is not enough and using 'read'
            # alone is not enough either. For example, it can allow searching
            # menu entries restricted to that user.
            try:
                pool.get('ir.model.access').check(cr, uid, model_name, 'read')
            except except_orm, e:
                continue
            if model_name == 'ir.attachment':
                attachment = pool.get(model_name).browse(cr, uid, id, context)
                if attachment.res_model and attachment.res_id:
                    if not pool.get(attachment.res_model).search(cr, uid, [('id','=',attachment.res_id)], context=context):
                        continue

            # Offset & limit can only be calulated once we have ensured the user has
            # access to those records.
            i = i + 1
            if i < offset:
                continue
            if i >= offset + limit:
                break

            # Search for the translation of the model
            model_label = pool.get('ir.translation')._get_source(cr, uid, 'ir.model,name', 'model', lang, model_label)
            if not model_label:
                model_label = x[2]

            d = self.headline( pool, cr, uid, text, id, model_id, model_name, context )
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

