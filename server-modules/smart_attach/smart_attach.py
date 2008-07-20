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
		'metainfo': fields.text('Meta Information')
	}

	# This is standard create but extracting meta information first
	def create(self, cr, uid, vals, context={}):
		if 'datas' in vals:
			m = self.extractMetaInfo( vals['datas'] )
			if m != None:
				vals['metainfo'] = m
		return super(ir_attachment, self).create(cr, uid, vals, context)

	# This is standard write but extracting meta information first
	def write(self, cr, uid, ids, vals, context={}):
		if 'datas' in vals:
			m = self.extractMetaInfo( vals['datas'] )
			if m == None:
				vals['metainfo'] = ''
			else:
				vals['metainfo'] = m
		return super(ir_attachment, self).write(cr, uid, ids, vals, context)

	# Extracts data from text nodes of an XML node list
	def getText(self, nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data + " "
		return rc

	# Extracts meta information from the given parameter which should be in base64
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
		else:
			# We couldn't get text information with strigi, let's try if it's an image
			os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', dir + '/object.tmp', dir + '/object.tif' )
			if os.path.exists( dir + '/object.tif' ):
				c = ocr.Classifier()
				c.prepareImage( dir + '/object.tif' )
				r = c.ocr()
				metaInfo = r['text'].strip()
				# TODO: Use language detection to choose different dictionary in TSearch2?
				# If so, that should apply to text/pdf/etc.. files too
				#r['language']
			else:
				metaInfo = None
		shutil.rmtree( dir, True )
		return metaInfo
ir_attachment()

