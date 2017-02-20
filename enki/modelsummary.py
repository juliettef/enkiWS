from google.appengine.ext.ndb import model


class EnkiModelSummary( model.Model ):

	name = model.StringProperty()
	count = model.IntegerProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	@classmethod
	def create( cls, name, count ):
		cls( name = name, count = count ).put_async()

	@classmethod
	def csv( cls ):
		list = cls.query().order( -cls.time_created, cls.name ).fetch()
		result = '"time_created","count","name"\n'
		for item in list:
			time_created = '"' + str(item.time_created).replace('"', "''") + '"'
			count = '"' + str( item.count ) + '"'
			name = '"' + str(item.name).replace('"', "''") + '"'
			result += ','.join([ time_created, count, name ]) + '\n'
		return result

