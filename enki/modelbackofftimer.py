from google.appengine.ext.ndb import model
import datetime


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
	identifier = model.StringProperty()
	last_failure = model.DateTimeProperty( )
	backoff_duration = TimeDeltaProperty()
