#!/usr/bin/python

def do_soprano():
	from PyKDE4.nepomuk import Nepomuk
	print "0"
	from PyKDE4.soprano import Soprano 
	fileName = 'test'
	manager = Nepomuk.ResourceManager.instance()
	print manager
	
	resource = Nepomuk.Resource( 'file://%s' % fileName, Soprano.Vocabulary.Xesam.File() )
	resource.setTags( [] ) # Nepomuk.Tag( tag ) for tag in tags
	resource.setRating( max(rating,0) )
	resource.setDescription( description )

	print resource

do_soprano()
