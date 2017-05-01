from google.appengine.ext.ndb import model


class EnkiModelThread( model.Model ):

	#=== MODEL ====================================================================

	author = model.IntegerProperty()
	title = model.StringProperty()

	forum = model.IntegerProperty()     # forum the thread belongs to

	num_posts = model.IntegerProperty( default = 0 )    # number of posts in the thread

	sticky_order = model.IntegerProperty( default = 0 )  # admin can set sticky_order > 0 to get threads 'stuck'

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	THREAD_TITLE_LENGTH_MAX = 200

	#=== QUERIES ==================================================================

	@classmethod
	def fetch_by_forum( cls, forum ):
		return cls.query( cls.forum == forum ).order( -cls.sticky_order, -cls.time_updated ).fetch()

	#=== UTILITIES ================================================================

