from google.appengine.ext.ndb import model

import enki.modelcounter


class EnkiModelSummary( model.Model ):

	name = model.TextProperty()
	count = model.IntegerProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	@classmethod
	def create( cls, name ):
		count = enki.modelcounter.get_count( name )
		entity =  EnkiModelSummary( name = name, count = count )
		entity.put_async()
