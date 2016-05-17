import datetime

import settings
import enki
import enki.libdisplayname
import enki.libforum
import enki.libfriends
import enki.libmessage
import enki.libuser
import enki.libutil
import enki.libdisplayname
import enki.librestapi
import enki.modeltokenverify
from enki import textmessages as MSG
from enki.modeluserpagedata import EnkiModelUserPageData


class HandlerBaseReauthenticate( enki.HandlerBase ):
# Force user reauthentication before posting data

	def get_logged_in( self ):
		if enki.libutil.is_debug():
			raise ValueError( 'This must be overriden in the derived class.' )


	def post_reauthenticated( self, params ):
		if enki.libutil.is_debug():
			raise ValueError( 'This must be overriden in the derived class.' )


	def get( self ):
		if self.ensure_is_logged_in() and not self.post_user_page_data():
			self.get_logged_in()


	def post( self ):
		self.check_CSRF()
		if self.ensure_is_logged_in() and self.ensure_is_reauthenticated():
			self.post_reauthenticated( self.request.params )


	def is_reauthenticated( self ):
		if self.is_logged_in():
			reauth_time = self.session.get( 'reauth_time' )
			if reauth_time and datetime.datetime.now() < ( reauth_time + datetime.timedelta( minutes = settings.REAUTH_EXPIRY )):
				return True
		return False


	def ensure_is_reauthenticated( self ):
		if not self.is_reauthenticated():
			self.save_user_page_data()
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REAUTHENTICATION_NEEDED())
			self.redirect( enki.libutil.get_local_url( 'reauthenticate' ))
			return False
		return True


	def save_user_page_data( self ):
		data = dict( self.request.params )
		route =  self.request.path
		entity = EnkiModelUserPageData.get_by_user_id_route( user_id = self.user_id, route = route )
		if entity:
			entity.data = data
		else:
			entity = EnkiModelUserPageData( user_id = self.user_id, route = route, data = data )
		entity.put()


	def post_user_page_data( self ):
	# post saved data if there is some corresponding to the page and the user is reauthenticated
		if self.is_reauthenticated():
			route =  self.request.path
			entity = EnkiModelUserPageData.get_by_user_id_route( user_id = self.user_id, route = route )
			if entity:
				post_data = entity.data
				entity.key.delete()
				self.post_reauthenticated( post_data )
				return True
		return False
