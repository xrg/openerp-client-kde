#!/usr/bin/python

import sys
import polib
from datetime import datetime

if len(sys.argv) != 2:
	print "Syntax: %s file.po" % sys.argv[0]
	sys.exit(1)

filename = sys.argv[1]

po = polib.pofile( filename )

to_remove = []
d = {}
for entry in po: 
	if entry.msgid in d:
		new_entry = d[entry.msgid]
		new_entry.occurrences += entry.occurrences
		new_entry.comment += '\n' + entry.comment 
	else:
		new_entry = polib.POEntry( msgid=entry.msgid )
		new_entry.occurrences = entry.occurrences
		new_entry.comment = entry.comment
		d[entry.msgid] = new_entry
	to_remove.append( entry )

for entry in to_remove:
	po.remove( entry )

#now = datetime.now().strftime( '%Y-%m-%-d %M:%S' )
#d[''].msgstr = "Project-Id-Version: PACKAGE VERSION\nReport-Msgid-Bugs-To: \nPOT-Creation-Date: %s+0200\nPO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\nLast-Translator: FULL NAME <EMAIL@ADDRESS>\nLanguage-Team: LANGUAGE <LL@li.org>\nMIME-Version: 1.0\nContent-Type: text/plain; charset=utf-8" % now

for entry in d.values():
	po.append( entry )

po.header = ""

po.save()

