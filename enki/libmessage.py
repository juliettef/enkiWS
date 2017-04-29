import collections

import enki.libdisplayname
from enki.modelmessage import EnkiModelMessage


messageData = collections.namedtuple( 'message_data', 'message_id, type, sender' )


def get_messages( user_id ):
	list = EnkiModelMessage.fetch_by_recipient( user_id )
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
	message = EnkiModelMessage.get_by_id( message_id )
	if message:
		message.key.delete()


def remove_messages_crossed( sender_or_receiver_a_id, sender_or_receiver_b_id ):
	message_a = EnkiModelMessage.get_by_sender_recipient( sender_or_receiver_a_id, sender_or_receiver_b_id )
	message_b = EnkiModelMessage.get_by_sender_recipient( sender_or_receiver_b_id, sender_or_receiver_a_id )
	if message_a:
		if message_a.type == 'friend_request':
			message_a.key.delete()
	if message_b:
		if message_b.type == 'friend_request':
			message_b.key.delete()
