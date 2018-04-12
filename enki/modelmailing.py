from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import enki.libutil


class EnkiModelMailing( model.Model ):

	#=== MODEL ====================================================================

	mail = model.StringProperty( repeated = True )  # pairs of 1. email address | 2. mailing list

	#=== CONSTANTS ================================================================

	#=== QUERIES ==================================================================

	# @classmethod
	# def exist_by_email( cls, email ):
	# 	count = cls.query( cls.mail == email ).count( 1 )
	# 	return count > 0

	@classmethod
	def count_by_email( cls, email ):
		count = cls.query( cls.mail == email ).count()

	# @classmethod
	# def fetch_by_email( cls, email ):
	# 	return cls.query( cls.mail == email ).fetch()
	#
	# @classmethod
	# def exist_by_mail_list( cls, mail_list ):
	# 	count = cls.query( cls.mail == mail_list ).count( 1 )
	# 	return count > 0
	#
	# @classmethod
	# def count_by_mail_list( cls, mail_list ):
	# 	return cls.query( cls.mail == mail_list ).count()
	#
	# @classmethod
	# def get_key_by_mail_list( cls, mail_list ):
	# 	return cls.query( cls.mail == mail_list ).get( keys_only = True )

	#=== UTILITIES ================================================================

