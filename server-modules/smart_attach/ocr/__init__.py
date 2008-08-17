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

import sys
import os
import shutil
import tempfile
from string import *

# As we don't want to force the dependencies on new users we try to 
# import gamera and pyaspell, but don't throw an exception if they're 
# not available
modules = {}
try:
	from pyaspell import *
	modules['pyaspell'] = True
except:
	modules['pyaspell'] = False
	print "Module 'pyaspell' is not available. Consider installing it if you want to use tesseract2 for text recognition in images."

class Classifier:
	def ocr(self):
		return { 'text': self.tesseract2('en'), 'language': 'en' }

	# This function uses tesseract2 instead of tesseract1
	# The idea is to find out using brute force in which language
	# the image is and use the output of OCRing using the appropiate language.
	def ocr2(self):
		if not modules['pyaspell']:
			return { 'text': '', 'language': 'en' }

		# TODO: Add catalan
		langs = [ 'en', 'es', 'fr', 'it', 'de', 'nl' ]
		# By setting max -1 we ensure we pickup the first (english) entry
		# in case nothing returns a correct result
		max = -1
		bestText = ''
		bestLang = ''
		for i in langs:
			text = self.tesseract2(i)
			a = Aspell(('lang', i))
			c = 0
			for x in text.split():
				if a.check(x):
					c += 1
			if c > max:
				max = c
				bestText = text
				bestLang = i
		return { 'text': bestText, 'language': bestLang }

	# This function executes tesseract 1 and returns the output it returns.
	def tesseract1(self):
		try: 
			dir=tempfile.mkdtemp()
			filename = dir + '/tmp.tiff'
			self.onebit.save_tiff(filename)
			os.spawnlp(os.P_WAIT, 'tesseract', 'tesseract', filename, dir + '/tesseract' )	
			f=open(dir + '/tesseract.txt', 'r')
			data=f.read()
			shutil.rmtree(dir, True)
			return { 'text': data, 'language': 'en' }
		except:
			return { 'text': '', 'language': 'en' }

	# This function executes tesseract 2 with the given language and returns the output it returns.
	def tesseract2(self, language):
		# Match 2 letter to 3 letter standard used by tesseract-ocr
		langs={ 'en': 'eng', 'es': 'spa', 'fr': 'fra', 'it': 'ita', 'de': 'deu', 'nl': 'nld', 'ca': 'cat' }
		if not language in langs:
			return ''
		try:
			dir=tempfile.mkdtemp()
			os.spawnlp(os.P_WAIT, 'tesseract', 'tesseract', self.file, dir + '/tesseract', '-l', langs[language] )
			f=open(dir + '/tesseract.txt', 'r')
			data = f.read()
			shutil.rmtree(dir, True)
			return data
		except:
			return ''

	# Simply set the image we want to analyze. Note that tesseract
	# can only open grayscale 8 bit depth TIF files with '.tif' 
	# extension.
	def prepareImage( self, file ):
		self.file = file 

	def classify(self):
		pass

