from google.appengine.ext.ndb import model


class EnkiModelSummary( model.Model ):

	name = model.StringProperty()
	count = model.IntegerProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	@classmethod
	def create( cls, name, count ):
		entity =  EnkiModelSummary( name = name, count = count )
		entity.put_async()
