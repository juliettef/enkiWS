from webapp2_extras import security

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelEmailSubscriptions(model.Model):

	#=== MODEL ====================================================================

	email = model.StringProperty()
	newsletters = model.StringProperty( repeated = True )
	token = model.StringProperty()	# unsubscribe token

	time_created = model.DateTimeProperty( auto_now_add = True )
	time_updated = model.DateTimeProperty( auto_now = True )

	#=== CONSTANTS ================================================================

	#=== QUERIES ==================================================================

	@classmethod
	def exist_by_email( cls, email ):
		count = cls.query(cls.email == email).count( 1 )
		return count > 0

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
	def get_by_email_newsletter( cls, email, newsletter ):
		return cls.query( ndb.AND( cls.email == email, cls.newsletters == newsletter )).get()

	@classmethod
	def exist_by_token_newsletter( cls, token, newsletter ):
		count = cls.query( ndb.AND( cls.token == token, cls.newsletters == newsletter )).count( 1 )
		return count > 0

	@classmethod
	def fetch_keys_by_email( cls, email ):
		return cls.query( cls.email == email ).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def add_newsletter( cls, email, newsletter ):
		entity = cls.get_by_email_newsletter( email, newsletter )
		if entity:
			return entity.token
		else:
			existing_entity = cls.get_by_email( email )
			if existing_entity:
				# add the newsletter to the list
				existing_entity.newsletters.append( newsletter )
				existing_entity.put()
				return existing_entity.token
			else:
				# create a new entity
				token = security.generate_random_string( entropy = 256 )
				new_entity = cls( email = email, newsletters = [ newsletter ], token = token )
				new_entity.put()
				return token

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
	def remove_by_email( cls, email ):
		entities = cls.fetch_keys_by_email( email )
		if entities:
			ndb.delete_multi_async( entities )

	@classmethod
	def count_newsletters_by_email( cls, email ):
		count = 0
		entity = cls.get_by_email( email )
		if entity:
			count = len( entity.newsletters )
		return count

	@classmethod
	def get_mailgun_email_batches( cls, newsletter ):
		# get batches of email addresses and their respective recipient variables (unsubscribe tokens) for a given newsletter.
		# reference: https://documentation.mailgun.com/en/latest/user_manual.html#batch-sending
		BATCH_SIZE = 1000
		batches_emails = []
		batches_emails_recipient_variables = []
		results, next_cursor, more = cls.query( cls.newsletters == newsletter ).fetch_page( BATCH_SIZE )
		batch_emails = ''
		batch_emails_recipient_variables = {}
		for result in results:
			batch_emails += result.email + ', '
			batch_emails_recipient_variables[ result.email ] = { 'token' : result.token }
		batches_emails.append( batch_emails[:-2] )
		batches_emails_recipient_variables.append( batch_emails_recipient_variables )
		while( more and next_cursor ):
			cursor = next_cursor
			results, next_cursor, more = cls.query( cls.newsletters == newsletter ).fetch_page( BATCH_SIZE, start_cursor = cursor )
			batch_emails = ''
			batch_emails_recipient_variables = { }
			for result in results:
				batch_emails += result.email + ', '
				batch_emails_recipient_variables[ result.email ] = { 'token':result.token }
			batches_emails.append( batch_emails[:-2] )
			batches_emails_recipient_variables.append( batch_emails_recipient_variables )
		return batches_emails, batches_emails_recipient_variables
