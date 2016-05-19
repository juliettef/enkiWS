from google.appengine.ext.ndb import model


class EnkiModelUser( model.Model ):

# if logged in through enki auth, otherwise null
	email = model.StringProperty() # unique
	password = model.StringProperty()

# if logged in through external provider at least once, otherwise null. Format "provider:userId"
	auth_ids_provider = model.StringProperty( repeated = True ) # unique

# other
	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
	# logged_in_last
