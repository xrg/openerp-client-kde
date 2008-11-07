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
import base64
import xml.dom.minidom
import tempfile
import os
import shutil
import codecs
import re

import ocr
from PyQt4.QtCore import *

# This class overrides the default ir_attachment class and adds the ability to
# obtain text from the file. Text is extracted using strigi and if it fails
# it will try to treat the file as an image and OCR it.
# Information found is stored in a new field called 'metainfo' that if indexed
# using the Full Text Search module it can be used to find documents easily.
class ir_attachment(osv.osv):
	_name = 'ir.attachment'
	_inherit = 'ir.attachment'
	_columns = {
		'metainfo': fields.text('Meta Information', help='Text automatically extracted from the attached file.')
	}

	# This is standard create but extracting meta information first
	def create(self, cr, uid, vals, context={}):
		if 'datas' in vals:
			vals['metainfo'] = 'Processing document...'
		id = super(ir_attachment, self).create(cr, uid, vals, context)
		if 'datas' in vals:
			self.pool.get('ir.cron').create(cr, uid, {
				'name': 'Update attachment metainformation',
				'user_id': uid,
				'model': 'ir.attachment',
				'function': 'updateMetaInfo',
				'args': repr([ [id] ])
			})
		return id

	# This is standard write but extracting meta information first
	def write(self, cr, uid, ids, vals, context={}):
		if 'datas' in vals:
			vals['metainfo'] = 'Processing document...'
		ret = super(ir_attachment, self).write(cr, uid, ids, vals, context)
		if 'datas' in vals:
			self.pool.get('ir.cron').create(cr, uid, {
				'name': 'Update attachment metainformation',
				'user_id': uid,
				'model': 'ir.attachment',
				'function': 'updateMetaInfo',
				'args': repr([ ids ])
			})

	# Extracts data from text nodes of an XML node list
	def getText(self, nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data + " "
		return rc

	# Extracts meta information from the given parameter which should be in base64
	# Note that the returned parameter should always be an unicode string.
	def extractMetaInfo(self, data):
		# First of all we'll see what strigi can do for us. If there is a text tag
		# it means it's some kind of text file (plain text, pdf, ps, doc, odf, etc..)
		# Otherwise, we'll try to treat it as an image, and OCR it.
		if not data:
			return ''
		dir=tempfile.mkdtemp()
		buf = base64.decodestring(data)
		f = open('%s/object.tmp' % dir,'wb')
		f.write( buf )
		f.close()

		# Analyze strigi's xmlindexer output
		output = os.popen('xmlindexer %s' % dir).read()
		try:
			dom = xml.dom.minidom.parseString( output )
			tags = dom.getElementsByTagName( 'text' )
		except:
			tags = []
		if len(tags):
			metaInfo = self.getText(tags[0].childNodes).strip()
			if not isinstance( metaInfo, unicode ):
				metaInfo = unicode( self.getText(tags[0].childNodes).strip(), errors='ignore' )
		else:
			# We couldn't get text information with strigi, let's try if it's an image
			os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', dir + '/object.tmp', dir + '/object.tif' )
			if os.path.exists( dir + '/object.tif' ):
				c = ocr.Classifier()
				c.prepareImage( dir + '/object.tif' )
				r = c.ocr()
				metaInfo = unicode( r['text'].strip(), errors='ignore' )
				# TODO: Use language detection to choose different dictionary in TSearch2?
				# If so, that should apply to text/pdf/etc.. files too
				#r['language']
			else:
				metaInfo = None
		shutil.rmtree( dir, True )
		return metaInfo

	def updateMetaInfo(self, cr, uid, ids):
		for attachment in self.browse(cr, uid, ids):
			metainfo = self.extractMetaInfo( attachment.datas ) or ''
			# We use SQL directly to update metainfo so last modification time doesn't change.
			# This avoids messages in the GUI telling that the object has been modified in the
			# meanwhile. After all, the field is readonly in the GUI so no conflicts can occur.
			cr.execute("UPDATE ir_attachment SET metainfo=%s WHERE id=%d", (metainfo, attachment.id) )
		cr.commit()

ir_attachment()

