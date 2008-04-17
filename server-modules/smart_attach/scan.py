#!/usr/bin/python

import sys
import os
from string import *
import codecs

from gamera.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Character:
	def __init__(self):
		self.character = None
		self.box = None

class Ocr:
	file = ""

	def ocr(self):
		#os.spawnlp(os.P_WAIT, '/usr/bin/tesseract', '/usr/bin/tesseract', self.file, '/tmp/tesseract', '-l', 'spa' )
		os.spawnlp(os.P_WAIT, '/home/albert/prog/empresa/gamera/tesseract/tesseract/ccmain/tesseract', '/home/albert/prog/empresa/gamera/tesseract/tesseract/ccmain/tesseract', self.file, '/tmp/tesseract', '-l', 'spa' )
		f=codecs.open('/tmp/tesseract.txt', 'r', 'utf-8')
		content = f.read()
		f.close()
		return content

	def processTesseractOutput(self, input):
		output = []
		# Output example line: "w 116 1724 133 1736"
		# Coordinates start at bottom left corner but we convert this into top left.
		for x in input.split('\n'):
			if not x:
				continue
			line = x.split(' ')
			x1 = int(line[1])
			x2 = int(line[3])
			y1 = self.height - int(line[2])
			y2 = self.height - int(line[4])
			width = x2 - x1
			height = y1 - y2

			c = Character()
			c.character = line[0] 
			c.box = QRectF( x1, y2, width, height )
			output.append( c )
		return output

	def textInRegion(self, region):
		output = []
		for x in self.boxes:
			r = region.intersected(x.box)
			if r.isValid():
				output.append(x.character)
		# We always return unicode strings always
		return u''.join(output)
		
	def scan(self, file):
		# Loading
		image = load_image(file)
		self.width = image.data.ncols 
		self.height = image.data.nrows
		info = image_info(file)
		self.xResolution = info.x_resolution
		self.yResolution = info.y_resolution

		# Converting
		img = image.to_greyscale()
		# Thresholding 
		onebit = img.otsu_threshold()
		# Saving for tesseract processing
		onebit.save_tiff("/tmp/tmp.tif")
		self.file = "/tmp/tmp.tif"
		txt = lower( self.ocr() )
		if isinstance(txt,str):
			print "HEREKRJELRKJ"
		
		self.boxes = self.processTesseractOutput(txt)

def initOcrSystem():
	init_gamera()

#c = Ocr()
#print("--------------")
#print("Argument: " + sys.argv[-1] )
#c.scan( sys.argv[-1] )


