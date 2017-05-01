from google.appengine.ext.ndb import model


class EnkiModelUser( model.Model ):

	#=== MODEL ====================================================================

	# if logged in through enki auth, otherwise null
	email = model.StringProperty() # unique
	password = model.StringProperty()

	# if logged in through external provider at least once, otherwise null. Format "provider:userId"
	auth_ids_provider = model.StringProperty( repeated = True ) # unique

	# Roles
	roles = model.StringProperty( repeated = True )

	# other
	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )
	# logged_in_last

	#=== QUERIES ==================================================================

	@classmethod
	def count( cls ):
		count = EnkiModelUser.query().count()
		return count

	@classmethod
	def get_key_by_email( cls, email ):
		return cls.query(cls.email == email).get( keys_only = True )

	@classmethod
	def get_by_email( cls, email ):
		return cls.query( cls.email == email ).get()

	@classmethod
	def exist_by_auth_id( cls, auth_id ):
		count = cls.query(cls.auth_ids_provider == auth_id).count(1)
		return count > 0

	@classmethod
	def get_by_auth_id( cls, auth_id ):
		return cls.query(cls.auth_ids_provider == auth_id).get()

	#=== UTILITIES ================================================================

	@classmethod
	def exist_by_email( cls, email ):
		if email and email != 'removed':
			count = cls.query( cls.email == email ).count(1)
			return count > 0
		return False

	@classmethod
	def has_password_by_email( cls, email ):
		user = cls.get_by_email( email )
		if user.password:
			return True
		return False
