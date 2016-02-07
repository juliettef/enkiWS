import webapp2
import urllib

import webapp2_extras
from google.appengine.api import urlfetch
from webapp2_extras import security
from webapp2_extras.i18n import gettext as _

import settings
import enki
import enki.libutil
import enki.libstore
import enki.libuser
import enki.textmessages as MSG

from enki.modelproductkey import EnkiModelProductKey
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.extensions import Extension
from enki.extensions import ExtensionPage



products = { 'product_a': { 'displayname' : 'Product A', 'price' : 3.00 },
             'product_b' : { 'displayname' : 'Product B', 'price' : 0.00 },
             }

SECRET_FASTSPRING = '67Rbc2TphwLw8DGfmstdVmsx' # TODO: move to secrets
URL_PURCHASE_FASTSPRING = str( 'https://sites.fastspring.com/enkisoftware/product/avoyd' )


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html', False,
		                  active_menu = 'store',
		                  product = products[ 'product_a' ] )

	def post( self ):
		url = URL_PURCHASE_FASTSPRING
		if not SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
			url = enki.libutil.get_local_url( 'storeemulatefastspring' )
		if self.is_logged_in():
			purchaser_user_id = self.enki_user.key.id()
			token = security.generate_random_string( entropy = 256 )
			token_purchase = EnkiModelTokenVerify( token = token, user_id = purchaser_user_id, type = 'purchasebyuser' )
			token_purchase.put()
			url += str( '?referrer=' + token_purchase.token )
		self.redirect( url )


def xstr( value ):
	if not value:
		return ''
	else:
		return str( value ).encode( 'utf-8' )

def xint( value ):
	if not value:
		return 0
	else:
		return int( value )


class HandlerGenlicenceFastSpring( webapp2.RequestHandler ):

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
			quantity = xint( self.request.get( 'quantity' ))
			licence_keys = enki.libstore.generate_licence_keys( quantity )
			self.response.write( licence_keys )
			return
		self.abort( 404 )


class HandlerOrderCompleteFastSpring( webapp2.RequestHandler ):

	def get(self):
		self.post()

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:

			licence_key_bundle = xstr( self.request.get( 'licence_key' ))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			order_id = xstr(self.request.get( 'order_id' ))
			product_name = xstr( self.request.get( 'product_name' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			shop_name = xstr( self.request.get( 'shop_name' ))
			quantity = xint( self.request.get( 'quantity' ))

			purchaser_user_id = None
			token_purchasebyuser = xstr( self.request.get( 'referrer' ))
			if token_purchasebyuser:
				token = enki.libuser.get_VerifyToken_by_token_type( token_purchasebyuser, 'purchasebyuser' )
				if token:
					purchaser_user_id = token.user_id
					token.key.delete()

			is_test = self.request.get( 'is_test' )
			if is_test:
				order_type = 'test'
				if enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
					order_type = 'emulated'

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
						  referrer = xstr( self.request.get('referrer') ),
		                  active_menu = 'store',
						  purchase_price = '$3.00',
						  purchaser_email = 'user_email@provided_to_fastspring.com' ,
						  quantity = 2,
		                  product = 'product_a' )

	def post( self ):
		if not SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
			self.check_CSRF()

			product = xstr( self.request.get( 'product' ))
			quantity = xint( self.request.get('quantity'))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			licence_keys = 'not generated'
			user_id = ''
			emulator_order_id = 'EMULATED_' + webapp2_extras.security.generate_random_string( length = 10, pool = webapp2_extras.security.DIGITS )

			url = enki.libutil.get_local_url( 'genlicencefastspring' )
			form_fields = { 'secret': 'pretendsecret', 'quantity': str( quantity ) }
			form_data = urllib.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				licence_keys = result.content.replace( '-', '' )

			referrer = xstr( self.request.get( 'referrer' ))
			token = enki.libuser.get_VerifyToken_by_token_type( referrer, 'purchasebyuser' )
			if token:
				user_id = token.user_id
				token.key.delete()
			licence_key_display = []
			for item in licence_keys.split():
				item_dash = enki.libstore.insert_dashes_5_10( item )
				licence_key_display.append( item_dash )
			self.add_infomessage( 'info', MSG.INFORMATION(),'<h3>FastSpring Store Emulator - Step 1</h3>'+
									'<h4>Emulated purchase details</h4>' +
									'<ul>' +
										'<li>&lt;EnkiModelProductKey&gt; #{FastSpring variable} = <em>&lt;emulated value&gt;</em></li>' +
										'<li>product_name #{orderItem.productName} = <em>' + product + '</em></li>' +
			                            '<li>order_id #{order.id} = <em>' + emulator_order_id + '</em></li>' +
			                            '<li>quantity #{orderItem.quantity} = <em>' + xstr( quantity ) + '</em></li>' +
			                            '<li>purchase_price #{orderItem.totalUSD} = <em>' + purchase_price + '</em></li>' +
			                            '<li>purchaser_email #{order.customer.email} = <em>' + purchaser_email + '</em></li>' +
										'<li>shop_name = <em>Emulator_FastSpring</em></li>' +
			                            '<li>licence_key #{orderItem.fulfillment.licence.licences.list} = <br><em><b>' + '<br>'.join( licence_key_display ) + '</b></em></li>' +
									'</ul>'
									'<h4>Internal data - generated if the purchaser was logged in when they bought the product</h4>' +
									'<ul>' +
										'<li>EnkiModelTokenVerify.user_id = purchaser user_id = <em>' + ( xstr( user_id ) if user_id else 'None' ) + '</em></li>' +
			                            '<li>EnkiModelTokenVerify.type purchasebyuser referrer #{order.referrer} = <em>' + ( xstr( referrer ) if referrer else 'None' ) + '</em></li>' +
			                        '</ul>' )

			url = enki.libutil.get_local_url( 'ordercompletefastspring' )
			form_fields = { 'licence_key' : licence_keys,
			                'purchase_price' : purchase_price,
			                'order_id' : emulator_order_id,
							'product_name' : product,
							'purchaser_email' : purchaser_email,
							'shop_name' : 'Emulator_FastSpring',
							'quantity' : quantity ,
			                'referrer' : referrer,
			                'is_test' : True }

			form_data = urllib.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				self.add_infomessage( 'success', MSG.SUCCESS(),'<h3>FastSpring Store Emulator - Step 2</h3><p>Purchase records created<p>' )
			else:
				self.add_infomessage( 'warning', MSG.WARNING(),'<h3>FastSpring Store Emulator - Step 2 FAILED: Purchase records not created</h3>' )

			self.redirect_to_relevant_page()


class ExtensionPageProducts( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'store', template_include = 'incproducts.html' )

	def get_data( self, handler ):
		data = [ 'product_a', 'product_b' ]
		return data


class ExtensionPageLibrary( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'inclibrary.html' )

	def get_data( self, handler ):
		licences_to_activate = []
		# licences purchased by the user, available to activate or give. The user can only activate one licence per product. Licences activated by another user don't appear.
		licences_to_give = []
		# licences purchased by the user, available to give only as the user already activated a licence for the same product.
		licences_activated = []
		# licences activated byt the user (user purchased or received as gift).
		if handler.is_logged_in():
			user_id = handler.enki_user.key.id()
			list_purchased = enki.libstore.fetch_EnkiProductKey_by_purchaser( user_id )
			if list_purchased:
				for i, item in enumerate( list_purchased ):
					item_licence_key = enki.libstore.insert_dashes_5_10( item.licence_key )
					if item.activated_by_user and item.activated_by_user == user_id:
						licences_activated.append([ item.product_name, item_licence_key ])
					else:
						licences_to_activate.append([ item.product_name , item_licence_key ])
		error = handler.session.pop( 'error_library', None )
		data = [ licences_to_activate, licences_activated, error ]
		return data


class HandlerLibrary( enki.HandlerBase ):

	def post( self ):
		self.check_CSRF()
		if self.is_logged_in():
			user_id = self.enki_user.key.id()
		licence_key_preset = self.request.get( 'licence_key_preset' )
		licence_key_manual = self.request.get( 'licence_key_manual' )
		licence_key = licence_key_preset
		is_manual = False
		if not licence_key_preset and licence_key_manual:
			licence_key = licence_key_manual
			is_manual = True
		if licence_key:
			item = enki.libstore.get_EnkiProductKey_by_licence_key( licence_key )
			if not item:
				if is_manual:
					self.session[ 'error_library' ] = _( 'Invalid licence key.' )
			elif item:
				if not item.activated_by_user:
					# the licence key is not activated.
					if enki.libstore.exist_EnkiProductKey_product_activated_by( user_id, item.product_name ):
						# the user has already activated a key for the same product
						if is_manual:
							self.session[ 'error_library' ] = _( 'You already own %(product)s.', product = item.product_name )
					else:
						# activate the licence
						item.activated_by_user = user_id
						item.put()
						self.add_infomessage( 'success', MSG.SUCCESS(), _( 'licence activated.' ))
				elif item.activated_by_user == user_id:
					# the user has already activated this specific key
					if is_manual:
						self.session[ 'error_library' ] = _( 'You already activated %(product)s. Do you want to give your spare licence to a friend ? Licence key: %(licence)s', product = item.product_name, licence = licence_key )
					else:
						self.add_infomessage( 'info', MSG.INFORMATION(), _( 'You already activated %(product)s. Do you want to give your spare licence to a friend ? Licence key: %(licence)s', product = item.product_name, licence = licence_key ))
				else:
					# another user has activated the key
					if is_manual:
						self.session[ 'error_library' ] = _( 'Another user already activated %(product)s licence %(licence)s.', product = item.product_name, licence = licence_key )
					else:
						self.add_infomessage( 'info', MSG.INFORMATION(), _( 'Another user already activated %(product)s licence %(licence)s.', product = item.product_name, licence = licence_key ))
		self.redirect_to_relevant_page()


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' ),
		          webapp2.Route( '/genlicencefastspring', HandlerGenlicenceFastSpring, name = 'genlicencefastspring' ),
		          webapp2.Route( '/ordercompletefastspring', HandlerOrderCompleteFastSpring, name = 'ordercompletefastspring' ),
		          webapp2.Route( '/storeemulatefastspring', HandlerStoreEmulateFastSpring, name = 'storeemulatefastspring' ),
		          webapp2.Route( '/library', HandlerLibrary, name = 'library' )
		          ]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
