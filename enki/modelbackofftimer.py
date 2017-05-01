import datetime
from google.appengine.ext.ndb import model


# define property subclass to store timedelta
# http://stackoverflow.com/questions/2413144/timedelta-convert-to-time-or-int-and-store-it-in-gae-python-datastore
# https://cloud.google.com/appengine/docs/python/ndb/subclassprop
def timedelta_to_microseconds( td ):
	return td.microseconds + ( td.seconds + td.days * 86400 ) * 1000000


class TimeDeltaProperty( model.IntegerProperty ):
	def _to_base_type( self, value ):
		return timedelta_to_microseconds( value )

	def _from_base_type( self, value ):
		if value is not None:
			return datetime.timedelta( microseconds = value )


class EnkiModelBackoffTimer( model.Model ):
# protect password entry against brute force attack

	#=== MODEL ====================================================================

	identifier = model.StringProperty()
	last_failure = model.DateTimeProperty( )
	backoff_duration = TimeDeltaProperty()

	#=== QUERIES ==================================================================

	@classmethod
	def exist_by_identifier( cls, identifier ):
		count = cls.query(cls.identifier == identifier).count(1)
		return count > 0

	@classmethod
	def get_by_identifier( cls, identifier ):
		return cls.query( cls.identifier == identifier ).get()

	@classmethod
	def fetch_keys_old( cls, days_old ):
		return cls.query( cls.last_failure <= (datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def add( cls, identifier ):
		if not cls.exist_by_identifier( identifier ):
			entity = cls( identifier = identifier, last_failure = datetime.datetime.now(), backoff_duration = datetime.timedelta( milliseconds = 15 ))
			entity.put()

	@classmethod
	def get( cls, identifier, increment = False ):
		entity = cls.get_by_identifier( identifier )
		if entity:
			result = entity.last_failure - datetime.datetime.now() + entity.backoff_duration
			if result <= datetime.timedelta( 0 ):
				# inactive backoff timer. Increase the delay.
				if increment:
					entity.backoff_duration += entity.backoff_duration
					entity.last_failure = datetime.datetime.now()
					entity.put()
				return 0
			else:
				return result
		else:
			if increment:
				cls.add( identifier )
			return 0

	@classmethod
	def remove( cls, identifier ):
		entity = cls.query( cls.identifier == identifier ).get()
		if entity:
			entity.key.delete()
