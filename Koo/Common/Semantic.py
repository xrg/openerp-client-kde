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

from Koo.Common import Common
from Koo import Rpc

def addInformationToFile( fileName, model, ids, field = None ):
	if not Common.isKdeAvailable:
		return
	if not isinstance(ids, list):
		ids = [ids]
	field = False
	try:
		# Obtain ratings 
		ratings = Rpc.session.call( '/semantic', 'rating', model, ids, field, Rpc.session.context )
		# Obtain all tags
		allTags = Rpc.session.call( '/semantic', 'tags', model, ids, field, Rpc.session.context )
		# Obtain all descriptions
		allDescriptions = Rpc.session.call( '/semantic', 'description', model, ids, field, Rpc.session.context )
		# Obtain all contacts
		allContacts = Rpc.session.call( '/semantic', 'contacts', model, ids, field, Rpc.session.context )
	except:
		ratings = {}
		allTags = {}
		allDescriptions = {}
		allContacts = {}

	# Calculate average rating
	rating = 0
	if ratings:
		for x in ratings.values():
			rating += x
		rating = rating / len(ratings)
	# Pickup all tags
	tags = []
	for x in allTags.values():
		tags += x
	tags = list( set( tags ) )
	# Pickup all descriptions and merge them into one
	description = '\n--\n'.join( set(allDescriptions.values()) )
	# Pickup all contacts 
	contacts = []
	for x in allContacts.values():
		contacts += x
	contacts = list( set( contacts ) )

	from PyKDE4.nepomuk import Nepomuk
	from PyKDE4.soprano import Soprano 

	resource = Nepomuk.Resource( 'file://%s' % fileName, Soprano.Vocabulary.Xesam.File() )
	resource.setTags( [Nepomuk.Tag( tag ) for tag in tags] )
	resource.setRating( max(rating,0) )
	resource.setDescription( description )
	if not resource.isValid():
		return

	manager = Nepomuk.ResourceManager.instance()
	# We cannot use manager.mainModel() because bindings for that function do not exist yet.
	# So Sebastian suggested this workaround.
	client = Soprano.Client.DBusClient( 'org.kde.NepomukStorage' )
	models = client.allModels()
	if not models:
		return
	model = client.createModel( models[0] )

	emails = [ '<mailto:%s>' % contact for contact in contacts ]
	emails = ', '.join( emails )
	if emails:
		# Search if there are any contacts on user's addresses with these e-mails.
		#iterator = model.executeQuery( "PREFIX nco: <http://www.semanticdesktop.org/ontologies/2007/03/22/nco#> SELECT ?name WHERE { ?contact nco:hasEmailAddress ?o. ?contact nco:fullname ?name }", Soprano.Query.QueryLanguageSparql )
		iterator = model.executeQuery( "PREFIX nco: <http://www.semanticdesktop.org/ontologies/2007/03/22/nco#> SELECT ?contact WHERE { ?contact nco:hasEmailAddress %s. }" % emails, Soprano.Query.QueryLanguageSparql )
		while iterator.next():
			x = iterator.binding('contact')
			if x.isResource():
				# Commented beacause it hangs Nepomuk when using sesame2 backend in my computer 
				#resource.addIsRelated( Nepomuk.Resource( x.uri() ).pimoThing() )
				pass

