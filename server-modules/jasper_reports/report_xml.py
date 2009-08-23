##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
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

import os
import csv
import copy
import base64
import report
import pooler
from osv import orm, osv, fields
import tools
import tempfile 
import codecs
import sql_db
import netsvc

# Inherit ir.actions.report.xml and add an action to be able to store .jrxml and .properties
# files attached to the report so they can be used as reports in the application.
class report_xml(osv.osv):
	_name = 'ir.actions.report.xml'
	_inherit = 'ir.actions.report.xml'
	_columns = {
		'jasper_output': fields.selection([('html','HTML'),('csv','CSV'),('xls','XLS'),('rtf','RTF'),('odt','ODT'),('ods','ODS'),('txt','Text'),('pdf','PDF')], 'Jasper Output'),
	}
	_defaults = {
		'jasper_output': lambda *a: 'pdf',
	}

	def update(self, cr, uid, ids, context={}):
		for report in self.browse(cr, uid, ids):
			attachmentIds = self.pool.get('ir.attachment').search( cr, uid, [('res_model','=','ir.actions.report.xml'),('res_id','=',report.id)], context=context)	
			has_jrxml = False
			# Browse attachments and store .jrxml and .properties into jasper_reports/custom_reports
			# directory. Also add or update ir.values data so they're shown on model views.
			for attachment in self.pool.get('ir.attachment').browse( cr, uid, attachmentIds ):
				content = attachment.datas
				fileName = attachment.datas_fname
				if not fileName or not content:
					continue
				if '.jrxml' in fileName:
					if has_jrxml:
						raise osv.except_osv(_('Error'), _('There are two .jrxml files attached to this report.'))
					has_jrxml = True
					path = self.save_file( fileName, content )
					# Update path into report_rml field.
					self.write(cr, uid, [report.id], {
						'report_rml': path
					})
					valuesId = self.pool.get('ir.values').search(cr, uid, [('value','=','ir.actions.report.xml,%s'% report.id)])
					data = {
						'name': report.name,
						'model': report.model,
						'key': 'action',
						'object': True,
						'key2': 'client_print_multi',
						'value': 'ir.actions.report.xml,%s'% report.id
					}
					if not valuesId:
						valuesId = self.pool.get('ir.values').create(cr, uid, data, context=context)
					else:
						self.pool.get('ir.values').write(cr, uid, valuesId, data, context=context)
						valuesId = valuesId[0]
				elif '.properties' in fileName:
					self.save_file( fileName, content )

				# Ensure the report is registered so it can be immediately used
				register_jasper_report( report.report_name, report.model )
		return True

	def save_file(self, name, value):
		path = os.path.abspath( os.path.dirname(__file__) )
		path += '/custom_reports/%s' % name
		f = open( path, 'wb+' )
		f.write( base64.decodestring( value ) )
		f.close()

		path = 'jasper_reports/custom_reports/%s' % name
		return path

report_xml()
