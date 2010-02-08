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

import time

from osv import osv, fields
import base64
import xml.dom.minidom
from lxml import etree
import tempfile
import os
import shutil
import codecs
import re
import threading
import pooler

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
	def create(self, cr, uid, vals, context=None):
		if 'datas' in vals:
			if vals['datas']:
				vals['metainfo'] = 'Processing document...'
			else:
				vals['metainfo'] = ''
		id = super(ir_attachment, self).create(cr, uid, vals, context)
		if 'datas' in vals:
			ctx = context and context.copy() or None
			thread = threading.Thread(target=updateMetaInfo, args=(cr.dbname, uid, [id]))
			thread.start()
		return id

	# This is standard write but extracting meta information first
	def write(self, cr, uid, ids, vals, context=None):
		if 'datas' in vals:
			if vals['datas']:
				vals['metainfo'] = 'Processing document...'
			else:
				vals['metainfo'] = ''
		ret = super(ir_attachment, self).write(cr, uid, ids, vals, context)
		if 'datas' in vals:
			ctx = context and context.copy() or None
			thread = threading.Thread(target=updateMetaInfo, args=(cr.dbname, uid, [ids]))
			thread.start()
		return ret

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
		try:
			f.write( buf )
		finally:
			f.close()

		# Analyze strigi's xmlindexer output
		f = os.popen('xmlindexer %s' % dir, 'r')
		try:
			output = f.read()
		finally:
			f.close()

		# Define namespaces
		metaInfo = None
		mimeTypes = []
		strigiText = None
		try:
			doc = etree.fromstring( output )
			tags = doc.xpath( '//file/text/text()' )
			if tags:
				strigiText = tags[0].strip()
			tags = doc.xpath( "//file/value[@name='http://freedesktop.org/standards/xesam/1.0/core#mimeType']/text()" )
			mimeTypes += tags
			# Newer versions use semanticdestkop.org ontologies.
			tags = doc.xpath( "//file/value[@name='http://www.semanticdesktop.org/ontologies/2007/01/19/nie#mimeType']/text()" )
			mimeTypes += tags
		except:
			pass

		if 'application/pdf' in mimeTypes:
			f = os.popen( 'pdftotext -enc UTF-8 -nopgbrk %s/object.tmp -' % dir, 'r')
			try:
				metaInfo = f.read()
			finally:
				f.close()
		elif 'application/vnd.oasis.opendocument.text' in mimeTypes:
			f = os.popen( 'odt2txt --encoding=UTF-8 %s/object.tmp' % dir, 'r' )
			try:
				metaInfo = f.read()
			finally:
				f.close()
		elif 'application/x-ole-storage' in mimeTypes:
			f = os.popen( 'antiword %s/object.tmp' % dir, 'r' )
			try:
				metaInfo = f.read()
			finally:
				f.close()

		# Test it at the very end in case some of the applications (pdftotext, odt2txt or antiword)
		# are not installed.
		if not metaInfo:
			metaInfo = strigiText

		if not metaInfo:
			# We couldn't get text information with other methods, let's see if it's an image
			os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', dir + '/object.tmp', dir + '/object.tif' )
			if os.path.exists( dir + '/object.tif' ):
				c = ocr.Classifier()
				c.prepareImage( dir + '/object.tif' )
				r = c.ocr()
				metaInfo = r['text'].strip()
				# TODO: Use language detection to choose different dictionary in TSearch2?
				# If so, that should apply to text/pdf/etc.. files too
				#r['language']

		if isinstance( metaInfo, str ):
			metaInfo = unicode( metaInfo, 'utf-8', errors='ignore' )
		shutil.rmtree( dir, True )
		return metaInfo


ir_attachment()

def updateMetaInfo(db_name, uid, ids):
	# As we're creating a new transaction, if update is executed in another thread and very fast,
	# it may not get latest changes. So we wait a couple of seconds before updating meta information.
	time.sleep( 2 )

	db, pool = pooler.get_db_and_pool(db_name)
	cr = db.cursor()

	# Ensure all ids still exist when data is actually updated:
	# Given this function is called in another process there're chances
	# the record might have been removed which would cause an 
	# exception when browsing.
	ids = pool.get('ir.attachment').search(cr, uid, [('id','in',ids)])
	for attachment in pool.get('ir.attachment').browse(cr, uid, ids):
		metainfo = pool.get('ir.attachment').extractMetaInfo( attachment.datas ) or ''
		# We use SQL directly to update metainfo so last modification time doesn't change.
		# This avoids messages in the GUI telling that the object has been modified in the
		# meanwhile. After all, the field is readonly in the GUI so no conflicts can occur.
		cr.execute("UPDATE ir_attachment SET metainfo=%s WHERE id=%s", (metainfo, attachment.id) )
	cr.commit()

