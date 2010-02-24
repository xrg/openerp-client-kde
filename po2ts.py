#!/usr/bin/python

import sys
import polib
from datetime import datetime
import tempfile

if len(sys.argv) != 3:
	print "Syntax: %s file.po file.ts" % sys.argv[0]
	sys.exit(1)

filename = sys.argv[1]
new_filename = sys.argv[2]

po = polib.pofile( filename )

to_remove = []
d = {}

contexts = {}
for entry in po: 
	comments = entry.comment.split('\n')
	for position in xrange( len(entry.occurrences) ):
		occurrence = entry.occurrences[position]	
		context = comments[position]
		contexts.setdefault(context, [])
		contexts[context].append( {
			'msgid': entry.msgid,
			'msgstr': entry.msgstr,
			'occurrence': occurrence,
		} )
		#new_entry = polib.POEntry( msgid=entry.msgid, msgstr=entry.msgstr )
		#new_entry.occurrences = [ occurrence ]
		#new_entries.append( new_entry )
	to_remove.append( entry )

# Remove all entries
for entry in to_remove:
	po.remove( entry )

# Add all new entries
#for entry in new_entries:
#	po.append( entry )

from xml.dom.minidom import Document

# Create the minidom document
doc = Document()

root = doc.createElement("TS")
root.setAttribute("version", "1.1")
doc.appendChild( root )
for key, contextList in contexts.iteritems():
	for context in contextList:
		xmlContext = doc.createElement('context')
		root.appendChild( xmlContext )


		xmlName = doc.createElement('name')
		xmlValue = doc.createTextNode( key.split(' ')[1] )
		xmlName.appendChild( xmlValue )

		xmlMessage = doc.createElement('message')

		xmlLocation = doc.createElement('location')
		xmlLocation.setAttribute('filename', context['occurrence'][0] )
		xmlLocation.setAttribute('line', context['occurrence'][1] )

		xmlSource = doc.createElement('source')
		xmlValue = doc.createTextNode( context['msgid'] )
		xmlSource.appendChild( xmlValue )

		xmlTranslation = doc.createElement('translation')
		xmlValue = doc.createTextNode( context['msgstr'] )
		xmlTranslation.appendChild( xmlValue )

		xmlContext.appendChild( xmlName )
		xmlContext.appendChild( xmlMessage )

		xmlMessage.appendChild( xmlLocation )
		xmlMessage.appendChild( xmlSource )
		xmlMessage.appendChild( xmlTranslation )


print "Writing %s" % new_filename
import codecs
f = codecs.open( new_filename, 'w', 'utf-8' )
#f.write( doc.toprettyxml(indent='\t') )
f.write( doc.toxml() )
f.close()

#po.header = ""

#print "SAVING..."
#po.save()
#print "SAVED!"

