import webapp2
import re
import random

import webapp2_extras
from webapp2_extras import security
from google.appengine.api import urlfetch

import settings
import enki
import enki.libutil
import enki.libenkiDL
import enki.textmessages as MSG
import enki.modelcounter

from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modelproductkey import EnkiModelProductKey
from enki.extensions import Extension
from enki.extensions import ExtensionPage

from enki.libutil import xstr as xstr
from enki.libutil import xint as xint


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html', False,
		                  active_menu = 'store',
		                  product_displayname = settings.product_displayname )

	def post( self ):
		url = settings.URL_PURCHASE_FASTSPRING

		# ------
		# Requires enkiDL
		if self.request.get( 'download' ):
			ref_url = enki.libutil.get_local_url( 'store' )
			self.session[ 'sessionrefpath' ] = ref_url
			url_fetcher = ''
			if settings.URLS_ENKIDL:
				# shuffle then try to download from locations in sequence
				random.shuffle( settings.URLS_ENKIDL )
				for i in range( len( settings.URLS_ENKIDL )):
					url_enkiDL = settings.URLS_ENKIDL[ i ]
					item_to_download = 'product_a'
					url_fetcher = enki.libenkiDL.URLFetcher()
					url_fetcher.get_download_URL( url_enkiDL, settings.SECRET_ENKIDL, item_to_download, self.request.remote_addr )
					if not url_fetcher.error:
						enki.modelcounter.increment( 'downloads_product_a' )
						break
				if url_fetcher and url_fetcher.error:
					self.response.status_int = 500
					self.add_infomessage( MSG.WARNING(), MSG.DOWNLOAD_ERROR())
					self.redirect( 'info' )
					return
				url = url_fetcher.download_url
			else:
				self.add_infomessage( MSG.WARNING(), MSG.DOWNLOAD_ERROR())
				self.redirect( 'info' )
				return
		# -------

		else:
			if not settings.SECRET_FASTSPRING or enki.libutil.is_debug( ) or settings.ENKI_EMULATE_STORE:
				url = enki.libutil.get_local_url( 'storeemulatefastspring' )
			else:
				enki.modelcounter.increment( 'purchases_product_a' )
			if self.is_logged_in():
				purchaser_user_id = self.enki_user.key.id()
				token = security.generate_random_string( entropy = 256 )
				token_purchase = EnkiModelTokenVerify( token = token, user_id = purchaser_user_id, type = 'purchasebyuser' )
				token_purchase.put()
				url += '?referrer=' + token_purchase.token.encode('utf-8')
		self.redirect( url )


class HandlerGenerateLicenceFastSpring( webapp2.RequestHandler ):

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == settings.SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_EMULATE_STORE:
			quantity = xint( self.request.get( 'quantity' ))
			licence_keys = EnkiModelProductKey.generate_licence_keys( quantity )
			self.response.write( licence_keys )
			return
		self.abort( 404 )


class HandlerOrderCompleteFastSpring( webapp2.RequestHandler ):

	def get(self):
		self.post()

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == settings.SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_EMULATE_STORE:

			licence_key_bundle = xstr( self.request.get( 'licence_key' ))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			order_id = xstr(self.request.get( 'order_id' ))
			product_name = xstr( self.request.get( 'product_name' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			shop_name = xstr(self.request.get('shop_name'))
			quantity = xint( self.request.get( 'quantity' ))

			if secret == settings.SECRET_FASTSPRING:
				is_test = self.request.get( 'is_test' )
				if is_test.capitalize() == 'True':
					order_type = 'test'
				else:
					order_type = 'purchase'
			else:
				order_type = xstr( self.request.get( 'order_type' ))

			purchaser_user_id = None
			token_purchasebyuser = xstr( self.request.get( 'referrer' ))
			if token_purchasebyuser:
				token = EnkiModelTokenVerify.get_by_token_type( token_purchasebyuser, 'purchasebyuser' )
				if token:
					purchaser_user_id = token.user_id
					token.key.delete()

			licence_keys = licence_key_bundle.replace( '-', '' ).split()
			for licence_key in licence_keys:
				item = EnkiModelProductKey( licence_key = licence_key,
				                            purchase_price = purchase_price,
				                            order_id = order_id,
				                            product_name = product_name,
				                            purchaser_email = purchaser_email,
				                            shop_name = shop_name,
				                            quantity = quantity,
				                            purchaser_user_id = purchaser_user_id,
				                            order_type = order_type )
				item.put()
		return


class HandlerStoreEmulateFastSpring( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'storeemulatefastspring.html',
						  referrer = xstr( self.request.get( 'referrer' )),
		                  active_menu = 'store',
						  purchase_price = '$3.00',
						  purchaser_email = 'user_email@provided_to_fastspring.com',
						  quantity = 2,
		                  product = 'product_a',
						  order_type = 'test' )

	def post( self ):
		if not settings.SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_EMULATE_STORE:
			self.check_CSRF()

			product = xstr( self.request.get( 'product' ))
			quantity = xint( self.request.get( 'quantity' ))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			order_type = xstr( self.request.get( 'order_type' ))
			licence_keys = 'not generated'
			user_id = ''
			order_id = webapp2_extras.security.generate_random_string( length = 10, pool = webapp2_extras.security.DIGITS )

			url = webapp2.uri_for( 'generatelicencefastspring', _full = True )
			form_fields = { 'secret': 'pretendsecret', 'quantity': str( quantity )}
			form_data = enki.libutil.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				licence_keys = result.content.replace( '-', '' )

			referrer = xstr( self.request.get( 'referrer' ))
			token = EnkiModelTokenVerify.get_by_token_type( referrer, 'purchasebyuser' )
			if token:
				user_id = token.user_id
			licence_key_display = []
			for item in licence_keys.split():
				item_dash = EnkiModelProductKey.insert_dashes_5_10( item )
				licence_key_display.append( item_dash )
			self.add_infomessage( MSG.INFORMATION(), '<h3>FastSpring Store Emulator - Step 1</h3>' +
									'<h4>Emulated purchase details</h4>' +
									'<ul>' +
										'<li>&lt;EnkiModelProductKey&gt; #{FastSpring variable} = <em>&lt;emulated value&gt;</em></li>' +
										'<li>product_name #{orderItem.productName} = <em>' + product + '</em></li>' +
			                            '<li>order_id #{order.id} = <em>' + order_id + '</em></li>' +
			                            '<li>quantity #{orderItem.quantity} = <em>' + xstr( quantity ) + '</em></li>' +
			                            '<li>purchase_price #{orderItem.totalUSD} = <em>' + purchase_price + '</em></li>' +
			                            '<li>purchaser_email #{order.customer.email} = <em>' + purchaser_email + '</em></li>' +
			                            '<li>licence_key #{orderItem.fulfillment.licence.licences.list} = <br><em><b>' + '<br>'.join( licence_key_display ) + '</b></em></li>' +
										'<li>shop_name = <em>Emulator</em></li>' +
								  		'<li>order_type = <em>' + order_type + '</em></li>' +
									'</ul>'
									'<h4>Internal data - generated if the purchaser was logged in when they bought the product</h4>' +
									'<ul>' +
										'<li>EnkiModelTokenVerify.user_id = purchaser user_id = <em>' + ( xstr( user_id ) if user_id else 'None' ) + '</em></li>' +
			                            '<li>EnkiModelTokenVerify.type purchasebyuser referrer #{order.referrer} = <em>' + ( xstr( referrer ) if referrer else 'None' ) + '</em></li>' +
			                        '</ul>' )

			url = webapp2.uri_for( 'ordercompletefastspring', _full = True )
			form_fields = { 'licence_key' : licence_keys,
			                'purchase_price' : purchase_price,
			                'order_id' : order_id,
							'order_type': order_type,
							'product_name' : product,
							'purchaser_email' : purchaser_email,
							'shop_name' : 'Emulator',
							'quantity' : quantity,
			                'referrer' : referrer,
			                'is_test' : 'true' }

			form_data = enki.libutil.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				message_view_library = ''
				if self.is_logged_in():
					message_view_library = '<p><a href="/profile" class="alert-link">View and activate licence keys</a>.</p>'
				self.add_infomessage( MSG.INFORMATION(),'<h3>FastSpring Store Emulator - Step 2</h3><p>Purchase records created<p>' + message_view_library )
			else:
				self.add_infomessage( MSG.WARNING(),'<h3>FastSpring Store Emulator - Step 2 FAILED: Purchase records not created</h3>' )

			self.redirect_to_relevant_page()


class HandlerLicencesGenerateFree(enki.HandlerBase):

	def get( self ):
		self.render_tmpl( 'licencesgeneratefree.html' )

	def post( self ):
		self.check_CSRF()
		product = xstr( self.request.get( 'product' ))
		quantity = xint( self.request.get( 'quantity' ))
		order_type = xstr( self.request.get( 'order_type' ))
		purchaser_email = xstr( self.request.get( 'purchaser_email' ))
		purchaser_email = purchaser_email if purchaser_email else None
		purchaser_user_id = xint( self.request.get( 'purchaser_user_id' ))
		purchaser_user_id = purchaser_user_id if purchaser_user_id != 0 else None
		info = xstr( self.request.get( 'info' ))
		info = info if info else None

		order_id = webapp2_extras.security.generate_random_string(length = 10, pool = webapp2_extras.security.DIGITS)
		licence_keys = EnkiModelProductKey.generate_licence_keys( quantity )
		licence_keys = licence_keys.replace( '-', '' ).split()
		for licence_key in licence_keys:
			item = EnkiModelProductKey( licence_key = licence_key,
										order_id = order_id,
										product_name = product,
										shop_name = 'Generator',
										quantity = quantity,
										order_type = order_type,
										purchaser_email = purchaser_email,
										purchaser_user_id = purchaser_user_id,
										info = info
										)
			item.put()
		licence_key_display = []
		for item in licence_keys:
			item_dash = EnkiModelProductKey.insert_dashes_5_10( item )
			licence_key_display.append( item_dash )
		self.add_infomessage( MSG.INFORMATION(), '<h3>Licence keys generated</h3>' +
								 '<ul>' +
									'<li>product_name = <em>' + product + '</em></li>' +
									'<li>order_type = <em>' + order_type + '</em></li>' +
									'<li>order_id = <em>' + order_id + '</em></li>' +
									'<li>quantity = <em>' + xstr( quantity ) + '</em></li>' +
									'<li>Recipient mail (purchaser_email) = <em>' + ( purchaser_email if purchaser_email else 'none' )  + '</em></li>' +
									'<li>Recipient user id (purchaser_user_id) = <em>' + ( xstr( purchaser_user_id) if purchaser_user_id else 'none' ) + '</em></li>' +
									'<li>info = <em>' + ( info if info else 'none' ) + '</em></li>' +
									'<li>licence_key(s) = <br><em>' + '<br>'.join( licence_key_display ) + '</em></li>' +
								 '</ul>' )
		self.redirect( 'licencesgeneratefree' )


class ExtensionPageProducts( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'store', template_include = 'incproducts.html' )

	def get_data( self, handler ):
		data = []
		for key, value in settings.product_displayname.iteritems():
			data.append( value )
		return data


class ExtensionPageLibrary( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'inclibrary.html' )

	def get_data( self, handler ):
		if handler.ensure_is_logged_in():
			user_id = handler.enki_user.key.id()
			licences_activated =  EnkiModelProductKey.count_by_activator( user_id )
			licences_available_to_activate = EnkiModelProductKey.count_by_purchaser_not_activated( user_id )
			data = [ licences_available_to_activate, licences_activated ]
			return data


class HandlerLibrary( enki.HandlerBaseReauthenticate ):

	def get_logged_in( self ):
		self.render_tmpl( 'library.html',
						  active_menu = 'profile',
						  data = self.get_data())

	def post_reauthenticated( self, params ):
		licence_key_preset = params.get( 'licence_key_preset' )
		licence_key_manual = params.get( 'licence_key_manual' )
		user_id = self.enki_user.key.id()
		if EnkiModelBackoffTimer.get( str( user_id ), True ) == 0:
			licence_key_preset = licence_key_preset.strip()[ :( EnkiModelProductKey.LICENCE_KEY_DASHES_LENGTH + 4 )] if licence_key_preset else '' # 4 allows for some leading and trailing characters
			licence_key_manual = licence_key_manual.strip()[ :( EnkiModelProductKey.LICENCE_KEY_DASHES_LENGTH + 4 )] if licence_key_manual else ''
			licence_key = licence_key_manual
			is_manual = True
			if licence_key_preset and not licence_key_manual:
				licence_key = licence_key_preset
				is_manual = False
			if licence_key:
				if len( licence_key ) < EnkiModelProductKey.LICENCE_KEY_LENGTH:
					self.session[ 'error_library' ] = MSG.LICENCE_TOO_SHORT()
					self.session[ 'error_library_licence' ] = licence_key
				elif len( licence_key ) <= ( EnkiModelProductKey.LICENCE_KEY_DASHES_LENGTH ):
					licence_key_reduced = re.sub( r'[^\w]', '', licence_key )[:EnkiModelProductKey.LICENCE_KEY_LENGTH ]
					item = EnkiModelProductKey.get_by_licence_key( licence_key_reduced )
					if not item:
						if is_manual:
							self.session[ 'error_library' ] = MSG.LICENCE_INVALID()
							self.session[ 'error_library_licence' ] = licence_key
					elif item:
						licence_key_formatted = EnkiModelProductKey.insert_dashes_5_10( licence_key_reduced )
						if item.activated_by_user == -1 :
							# the licence key is not activated.
							if EnkiModelProductKey.exist_product_by_activator( user_id, item.product_name ):
								# the user has already activated a key for the same product
								if is_manual:
									self.session[ 'error_library' ] = MSG.LICENCE_ALREADY_ACTIVATED_GIVE( settings.product_displayname[ item.product_name ])
									self.session[ 'error_library_licence' ] = licence_key_formatted
							else:
								# activate the licence
								item.activated_by_user = user_id
								item.put()
								EnkiModelBackoffTimer.remove( str( user_id ))
								self.add_infomessage( MSG.SUCCESS(), MSG.PRODUCT_LICENCE_ACTIVATED( settings.product_displayname[ item.product_name ], licence_key_formatted ))
						elif item.activated_by_user == user_id:
							# the user has already activated this specific key
							if is_manual:
								self.session[ 'error_library' ] = MSG.PRODUCT_ALREADY_ACTIVATED( settings.product_displayname[ item.product_name ])
								self.session[ 'error_library_licence' ] = licence_key_formatted
							else:
								self.add_infomessage( MSG.INFORMATION(), MSG.PRODUCT_ALREADY_ACTIVATED( settings.product_displayname[ item.product_name ]))
						else:
							# another user has activated the key
							if is_manual:
								self.session[ 'error_library' ] = MSG.LICENCE_ANOTHER_USER_ACTIVATED( settings.product_displayname[ item.product_name ], licence_key_formatted )
								self.session[ 'error_library_licence' ] = licence_key_formatted
							else:
								self.add_infomessage( MSG.INFORMATION(), MSG.LICENCE_ANOTHER_USER_ACTIVATED( settings.product_displayname[ item.product_name ], licence_key_formatted ))
				else:
					self.session[ 'error_library' ] = MSG.LICENCE_TOO_LONG()
					self.session[ 'error_library_licence' ] = licence_key
			elif is_manual:
				self.session[ 'error_library' ] = MSG.LICENCE_MISSING()
		else:
			backoff_timer = EnkiModelBackoffTimer.get( str( user_id ))
			if backoff_timer != 0:
				self.session[ 'error_library' ] = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))

		self.render_tmpl('library.html',
						 active_menu = 'profile',
						 data = self.get_data())

	def get_data( self ):
		user_id = self.enki_user.key.id()
		licences_to_activate = []
		# licences purchased by the user, available to activate or give. The user can only activate one licence per product. Licences activated by another user don't appear.
		licences_to_give = []
		# licences purchased by the user, available to give only as the user already activated a licence for the same product.
		licences_activated = []
		# licences activated byt the user (user purchased or received as gift).
		list_purchased = EnkiModelProductKey.fetch_by_purchaser( user_id )
		if list_purchased:
			for i, item in enumerate( list_purchased ):
				item_licence_key = EnkiModelProductKey.insert_dashes_5_10( item.licence_key )
				product_already_owned = EnkiModelProductKey.exist_product_by_activator( user_id, item.product_name )
				if item.activated_by_user == -1:
					if not product_already_owned:
						licences_to_activate.append([ item.product_name, item_licence_key, settings.product_displayname[ item.product_name ]])
					else:
						licences_to_give.append([ item.product_name, item_licence_key, settings.product_displayname[ item.product_name ]])
		list_activated = EnkiModelProductKey.fetch_by_activator(user_id)
		if list_activated:
			for i, item in enumerate( list_activated ):
				item_licence_key = EnkiModelProductKey.insert_dashes_5_10(item.licence_key)
				licences_activated.append([ item.product_name, item_licence_key, settings.product_displayname[ item.product_name ]])
		error = self.session.pop( 'error_library', None )
		licence_key_value = self.session.pop( 'error_library_licence', None )
		data = [ error, licences_to_activate, licences_to_give, licences_activated, licence_key_value ]
		return data


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' ),
		          webapp2.Route( '/generatelicencefastspring', HandlerGenerateLicenceFastSpring, name = 'generatelicencefastspring' ),
		          webapp2.Route( '/ordercompletefastspring', HandlerOrderCompleteFastSpring, name = 'ordercompletefastspring' ),
		          webapp2.Route( '/storeemulatefastspring', HandlerStoreEmulateFastSpring, name = 'storeemulatefastspring' ),
				  webapp2.Route( '/admin/licencesgeneratefree', HandlerLicencesGenerateFree, name = 'licencesgeneratefree' ),
		          webapp2.Route( '/library', HandlerLibrary, name = 'library' )
		          ]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', MSG.STORE())]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
