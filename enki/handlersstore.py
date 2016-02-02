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
		self.render_tmpl( 'store.html',
		                  active_menu = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ 'product_a' ] )

	def post( self ):
		self.check_CSRF()
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


class HandlerGenLicenseFastSpring( webapp2.RequestHandler ):

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
			quantity = xint( self.request.get( 'quantity' ))
			license_keys = enki.libstore.generate_license_keys( quantity )
			self.response.write( license_keys )
			return
		self.abort( 404 )


class HandlerOrderCompleteFastSpring( webapp2.RequestHandler ):

	def get(self):
		self.post()

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:

			license_key_bundle = xstr( self.request.get( 'license_key' ))
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

			is_test = self.request.get( 'is_test' )
			if is_test:
				order_type = 'test'
				if enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
					order_type = 'emulated'

			license_keys = license_key_bundle.split()
			for license_key in license_keys:
				item = EnkiModelProductKey( license_key = license_key,
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
		                  CSRFtoken = self.create_CSRF( 'storeemulatefastspring' ),
		                  product = products[ 'product_a' ] )

	def post( self ):
		if not SECRET_FASTSPRING or enki.libutil.is_debug() or settings.ENKI_SIMULATE_STORE:
			self.check_CSRF()

			product = 'product_a'
			quantity = xint( self.request.get('quantity'))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			license_keys = 'not generated'
			user_id = ''
			emulator_order_id = 'EMULATED_' + webapp2_extras.security.generate_random_string( length = 10, pool = webapp2_extras.security.DIGITS )

			url = enki.libutil.get_local_url( 'genlicensefastspring' )
			form_fields = { 'secret': 'pretendsecret', 'quantity': str( quantity ) }
			form_data = urllib.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				license_keys = result.content

			referrer = xstr( self.request.get( 'referrer' ))
			token = enki.libuser.get_VerifyToken_by_token_type( referrer, 'purchasebyuser' )
			if token:
				user_id = token.user_id
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
			                            '<li>license_key #{orderItem.fulfillment.license.licenses.list} = <br><em><b>' + '<br>'.join( xstr( license_keys ).split()) + '</b></em></li>' +
									'</ul>'
									'<h4>Internal data - generated if the purchaser was logged in when they bought the product</h4>' +
									'<ul>' +
										'<li>EnkiModelTokenVerify.user_id = purchaser user_id = <em>' + ( xstr( user_id ) if user_id else 'None' ) + '</em></li>' +
			                            '<li>EnkiModelTokenVerify.type purchasebyuser referrer #{order.referrer} = <em>' + ( xstr( referrer ) if referrer else 'None' ) + '</em></li>' +
			                        '</ul>' )

			url = enki.libutil.get_local_url( 'ordercompletefastspring' )
			form_fields = { 'license_key' : license_keys,
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
		data = [ 'Game1', 'Game2', 'Music1', 'Music2', 'Music3', 'Art1', 'Art2' ]
		return data


class ExtensionPageLibrary( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'inclibrary.html' )

	def get_data( self, handler ):
		products = []
		products_activated = []
		if handler.is_logged_in():
			user_id = handler.enki_user.key.id()
		list = enki.libstore.fetch_EnkiProductKey_by_purchaser( user_id )
		if list:
			for i, item in enumerate( list ):
				# product_dn = products[ item.product_name ]
				if item.activated_by_user and item.activated_by_user == user_id:
					products_activated.append([ item.product_name, item.license_key ])
				else:
					products.append([ item.product_name , item.license_key ])
		data = [ products, products_activated ]
		return data


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' ),
		          webapp2.Route( '/genlicensefastspring', HandlerGenLicenseFastSpring, name = 'genlicensefastspring' ),
		          webapp2.Route( '/ordercompletefastspring', HandlerOrderCompleteFastSpring, name = 'ordercompletefastspring' ),
		          webapp2.Route( '/storeemulatefastspring', HandlerStoreEmulateFastSpring, name = 'storeemulatefastspring' ) ]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
