from google.appengine.ext import ndb
from google.appengine.ext.ndb import model


class EnkiModelMessage( model.Model ):

	sender = model.IntegerProperty()
	recipient = model.IntegerProperty()
	type = model.StringProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	@classmethod
	def get_by_id( cls, message_id ):
		return ndb.Key( cls, message_id ).get()

	@classmethod
	def exist_by_recipient( cls, user_id ):
		count = cls.query( cls.recipient == user_id ).count( 1 )
		return count > 0

	@classmethod
	def count_by_recipient( cls, user_id ):
		return cls.query( cls.recipient == user_id ).count()

	@classmethod
	def fetch_by_recipient( cls, user_id ):
		return cls.query( cls.recipient == user_id ).fetch()

	@classmethod
	def exist_by_sender_recipient( cls, sender_id, recipient_id ):
		count = cls.query( ndb.AND( cls.sender == sender_id, cls.recipient == recipient_id )).count( 1 )
		return count > 0

	@classmethod
	def get_key_by_sender_recipient( cls, sender_id, recipient_id ):
		return cls.query( ndb.AND( cls.sender == sender_id, cls.recipient == recipient_id )).get( keys_only = True )

	@classmethod
	def get_by_sender_recipient( cls, sender_id, recipient_id ):
		return cls.query( ndb.AND( cls.sender == sender_id, cls.recipient == recipient_id )).get()

	@classmethod
	def exist_sent_or_received( cls, user_id ):
		count = cls.query( ndb.OR( cls.sender == user_id, cls.recipient == user_id )).count( 1 )
		return count > 0

	@classmethod
	def fetch_keys_sent_or_received( cls, user_id ):
		return cls.query( ndb.OR( cls.sender == user_id, cls.recipient == user_id )).fetch( keys_only = True )
