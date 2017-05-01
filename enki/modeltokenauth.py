import datetime

from google.appengine.ext.ndb import model


class EnkiModelTokenAuth( model.Model ):

	#=== MODEL ====================================================================

	token = model.StringProperty() # unique
	user_id = model.IntegerProperty() # the ndb ID nr
	time_created = model.DateTimeProperty( auto_now_add = True )

	#=== QUERIES ==================================================================

	@classmethod
	def fetch_keys_old( cls, days_old ):
		return cls.query( cls.time_created <= ( datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True )
