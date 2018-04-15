from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import enki.libutil


class EnkiModelMailing( model.Model ):

	#=== MODEL ====================================================================

	mail = model.StringProperty( repeated = True )  # pairs of 1. email address | 2. mailing list

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
	def exist_by_email_mailing_list( cls, email, mailing_list ):
		count = cls.query( ndb.AND( cls.mail == email, cls.mail == mailing_list )).count( 1 )
		return count > 0

	@classmethod
	def fetch_keys_by_email_mailing_list( cls, email, mailing_list ):
		return cls.query( ndb.AND( cls.mail == email, cls.mail == mailing_list )).fetch( keys_only = True )

	#=== UTILITIES ================================================================

	@classmethod
	def add_email_mailing( cls, email, mailing_list ):
		if not cls.exist_by_email_mailing_list( email, mailing_list ):
			mailing = cls( mail = [ email, mailing_list ])
			mailing.put()

	@classmethod
	def remove_email_mailing( cls, email, mailing_list ):
		entities = cls.fetch_keys_by_email_mailing_list( email, mailing_list )
		if entities:
			ndb.delete_multi( entities )
