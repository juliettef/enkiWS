from google.appengine.ext.ndb import model


class EnkiModelPost( model.Model ):
	
	#=== MODEL ====================================================================
	
	author = model.IntegerProperty()
	body = model.TextProperty()

	thread = model.IntegerProperty()    # thread the post belongs to

	sticky_order = model.IntegerProperty( default = 0 )  # admin can set sticky_order > 0 to get threads 'stuck'

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	POST_LENGTH_MAX = 10000
	POST_DELETED = '[deleted]'
	POSTS_PER_PAGE = 10
	POST_DEFAULT = 1
	POST_LAST = 'last'
	PAGES_BEFORE = 3
	PAGES_AFTER = 3

	ERROR_POST_LENGTH = -51
	ERROR_POST_CREATION = -52
	ERROR_POST_EDITION = -53
	ERROR_POST_DELETION = -54

	#=== QUERIES ==================================================================

	@classmethod
	def fetch_by_thread( cls, thread, limit, offset ):
		return cls.query( cls.thread == thread ).order( -cls.sticky_order, cls.time_created ).fetch( limit = limit, offset = offset )

	@classmethod
	def fetch_by_author( cls, author ):
		return cls.query( cls.author == author ).order( -cls.time_created ).fetch()

	@classmethod
	def fetch_key_by_author( cls, author ):
		return cls.query( cls.author == author ).fetch( keys_only = True )

	#=== UTILITIES ================================================================
