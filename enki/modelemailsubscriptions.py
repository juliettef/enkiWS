from webapp2_extras import security

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelEmailSubscriptions(model.Model):

	#=== MODEL ====================================================================

	email = model.StringProperty()
	newsletters = model.StringProperty( repeated = True )
	token = model.StringProperty()	# unsubscribe token

	#=== CONSTANTS ================================================================

	#=== QUERIES ==================================================================

	@classmethod
	def get_by_email( cls, email ):
		return cls.query(cls.email == email).get()

	@classmethod
	def get_by_token( cls, token ):
		return cls.query( cls.token == token ).get()

	@classmethod
	def exist_by_email_newsletter( cls, email, newsletter ):
		count = cls.query( ndb.AND( cls.email == email, cls.newsletters == newsletter )).count( 1 )
		return count > 0

	@classmethod
	def exist_by_token_newsletter( cls, token, newsletter ):
		count = cls.query( ndb.AND( cls.token == token, cls.newsletters == newsletter )).count( 1 )
		return count > 0

	@classmethod
	def fetch_keys_by_email_newsletter( cls, email, newsletter ):
		return cls.query( ndb.AND( cls.email == email, cls.newsletters == newsletter )).fetch( keys_only = True )

	@classmethod
	def fetch_keys_by_token( cls, token ):
		return cls.query( cls.token == token ).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def add_newsletter( cls, email, newsletter ):
		if not cls.exist_by_email_newsletter( email, newsletter ):
			existing_entity = cls.get_by_email( email )
			if existing_entity:
				# add the newsletter to the list
				existing_entity.newsletters.append( newsletter )
				existing_entity.put()
			else:
				# create a new entity
				token = security.generate_random_string( entropy = 256 )
				new_entity = cls( email = email, newsletters = [ newsletter ], token = token )
				new_entity.put()

	@classmethod
	def remove_newsletter_by_email( cls, email, newsletter ):
		if cls.exist_by_email_newsletter( email, newsletter ):
			entity = cls.get_by_email( email )
			if len( entity.newsletters ) == 1:
				# if no newsletter would be left after removal, delete the record
				entity.key.delete()
			else:
				# remove the newsletter.
				index = entity.newsletters.index( newsletter )
				del entity.newsletters[ index ]
				entity.put()

	@classmethod
	def remove_newsletter_by_token( cls, token, newsletter ):
		if cls.exist_by_token_newsletter( token, newsletter ):
			entity = cls.get_by_token( token )
			if len( entity.newsletters ) == 1:
				# if no newsletter would be left after removal, delete the record
				entity.key.delete()
			else:
				# remove the newsletter
				index = entity.newsletters.index( newsletter )
				del entity.newsletters[ index ]
				entity.put()

	@classmethod
	def count_newsletters_by_email( cls, email ):
		count = 0
		entity = cls.get_by_email( email )
		if entity:
			count = len( entity.newsletters )
		return count
