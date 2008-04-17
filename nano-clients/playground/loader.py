#!/usr/bin/python

import os
import sys
import glob
import base64
import rpc

if not sys.argv:
	print 'loader.py directory'
	sys.exit(1)

rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'g1' )

files = glob.glob(sys.argv[1] + "/*.png")
for x in files:
	print "Loading file: ", x 
	fields = {}
	fields['name'] = os.path.split(x)[1]
	fields['datas'] = base64.encodestring(file(x).read())
	rpc.session.execute('/object', 'execute', 'nan.document.queue', 'create', fields )
	
