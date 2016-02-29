from google.appengine.ext.ndb import model


class EnkiModelMessage( model.Model ):

	sender = model.IntegerProperty()
	recipient = model.IntegerProperty()
	type = model.StringProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )
