import collections

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

from enki.modeldisplayname import EnkiModelDisplayName


messageData = collections.namedtuple( 'message_data', 'message_id, type, sender' )


class EnkiModelMessage( model.Model ):

	#=== MODEL ====================================================================

	sender = model.IntegerProperty()
	recipient = model.IntegerProperty()
	type = model.StringProperty()
	time_created = model.DateTimeProperty( auto_now_add = True )

	#=== QUERIES ==================================================================

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

	#=== UTILITIES ================================================================

	@classmethod
	def send_message( cls, sender_id, recipient_id, type ):
		message = EnkiModelMessage( sender = sender_id, recipient = recipient_id, type = type )
		message.put()

	@classmethod
	def get_messages( cls, user_id ):
		list = cls.fetch_by_recipient( user_id )
		message_list = []
		if list:
			for i, item in enumerate( list ):
				entity = EnkiModelDisplayName.get_by_user_id_current( item.sender )
				sender = EnkiModelDisplayName.get_user_id_display_name_url( entity )
				type = item.type
				message_id = item.key.id()
				message = messageData( message_id, type, sender  )
				message_list.append( message )
			return message_list

	@classmethod
	def remove_message( cls, message_id ):
		message = cls.get_by_id( message_id )
		if message:
			message.key.delete()

	@classmethod
	def remove_messages_crossed( cls, sender_or_receiver_a_id, sender_or_receiver_b_id ):
		message_a = cls.get_by_sender_recipient( sender_or_receiver_a_id, sender_or_receiver_b_id )
		message_b = cls.get_by_sender_recipient( sender_or_receiver_b_id, sender_or_receiver_a_id )
		if message_a:
			if message_a.type == 'friend_request':
				message_a.key.delete()
		if message_b:
			if message_b.type == 'friend_request':
				message_b.key.delete()

	@classmethod
	def delete_user_messages( cls, user_id ):
		ndb.delete_multi( cls.fetch_keys_sent_or_received( user_id ))
