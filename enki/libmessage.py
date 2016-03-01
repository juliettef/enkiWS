import collections

from google.appengine.ext import ndb

import enki.libdisplayname
from enki.modelmessage import EnkiModelMessage


messageData = collections.namedtuple( 'message_data', 'message_id, type, sender' )


def get_messages( user_id ):
	list = fetch_EnkiMessage_by_recipient( user_id )
	message_list = []
	if list:
		for i, item in enumerate( list ):
			entity = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( item.sender )
			sender = enki.libdisplayname.get_user_id_display_name_url( entity )
			type = item.type
			message_id = item.key.id()
			message = messageData( message_id, type, sender  )
			message_list.append( message )
		return message_list


def remove_message( message_id ):
	message = get_EnkiMessage_by_id( message_id )
	if message:
		message.key.delete()


def remove_messages_crossed( sender_or_receiver_a_id, sender_or_receiver_b_id ):
	message_a = get_EnkiMessage_by_sender_recipient( sender_or_receiver_a_id, sender_or_receiver_b_id )
	message_b = get_EnkiMessage_by_sender_recipient( sender_or_receiver_b_id, sender_or_receiver_a_id )
	if message_a:
		if message_a.type == 'friend_request':
			message_a.key.delete()
	if message_b:
		if message_b.type == 'friend_request':
			message_b.key.delete()


#=== QUERIES ==================================================================


def exist_EnkiMessage_by_recipient( user_id ):
	count = EnkiModelMessage.query( EnkiModelMessage.recipient == user_id ).count( 1 )
	return count > 0


def fetch_EnkiMessage_by_recipient( user_id ):
	list = EnkiModelMessage.query( EnkiModelMessage.recipient == user_id ).fetch()
	return list


def get_key_EnkiMessage_by_sender_recipient( sender_id, recipient_id ):
	entity = EnkiModelMessage.query( ndb.AND( EnkiModelMessage.sender == sender_id,
	                                          EnkiModelMessage.recipient == recipient_id )).get( keys_only = True )
	return entity


def exist_EnkiMessage_by_sender_recipient( sender_id, recipient_id ):
	count = EnkiModelMessage.query( ndb.AND( EnkiModelMessage.sender == sender_id,
	                                         EnkiModelMessage.recipient == recipient_id )).count( 1 )
	return count > 0


def get_EnkiMessage_by_id( message_id ):
	entity = ndb.Key( EnkiModelMessage, message_id ).get()
	return entity


def get_EnkiMessage_by_sender_recipient( sender_id, recipient_id ):
	entity = EnkiModelMessage.query( ndb.AND( EnkiModelMessage.sender == sender_id,
	                                          EnkiModelMessage.recipient == recipient_id )).get()
	return entity


def exist_sent_or_received_message( user_id ):
	count = EnkiModelMessage.query( ndb.OR( EnkiModelMessage.sender == user_id,
	                                        EnkiModelMessage.recipient == user_id )).count( 1 )
	return count > 0
