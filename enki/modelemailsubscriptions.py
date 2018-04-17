from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelEmailSubscriptions(model.Model):

	#=== MODEL ====================================================================

	mail = model.StringProperty( repeated = True )  # email subscriptions in pairs of 1. email address | 2. newsletter name

	#=== CONSTANTS ================================================================

	#=== QUERIES ==================================================================

	@classmethod
	def exist_by_email( cls, email ):
		count = cls.query( cls.mail == email ).count( 1 )
		return count > 0

	@classmethod
	def count_by_email( cls, email ):
		return cls.query( cls.mail == email ).count()

	@classmethod
	def exist_by_email_newsletter( cls, email, newsletter ):
		count = cls.query(ndb.AND(cls.mail == email, cls.mail == newsletter)).count(1)
		return count > 0

	@classmethod
	def fetch_keys_by_email_newsletter( cls, email, newsletter ):
		return cls.query(ndb.AND(cls.mail == email, cls.mail == newsletter)).fetch(keys_only = True)

	#=== UTILITIES ================================================================

	@classmethod
	def add( cls, email, newsletter ):
		if not cls.exist_by_email_newsletter(email, newsletter):
			entity = cls(mail = [ email, newsletter ])
			entity.put()

	@classmethod
	def remove( cls, email, newsletter ):
		entities = cls.fetch_keys_by_email_newsletter(email, newsletter)
		if entities:
			ndb.delete_multi( entities )
