import webapp2
import urllib

from google.appengine.api import urlfetch
from webapp2_extras import security
from webapp2_extras.i18n import gettext as _

import enki
import enki.libutil
import enki.libstore
import enki.libuser

from enki.modelproductkey import EnkiModelProductKey
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.extensions import Extension
from enki.extensions import ExtensionPage



products = { 'avoyd': { 'displayname' : 'Avoyd', 'price' : 3.00 },
             'avoyd-1999' : { 'displayname' : 'Avoyd-1999', 'price' : 0.00 },
             }

SECRET_FASTSPRING = '67Rbc2TphwLw8DGfmstdVmsx' # TODO: move to secrets
URL_PURCHASE_FASTSPRING = str( 'https://sites.fastspring.com/enkisoftware/product/avoyd' )


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ 'avoyd' ] )

	def post( self ):
		self.check_CSRF( 'store' )
		url = URL_PURCHASE_FASTSPRING
		if not SECRET_FASTSPRING or enki.libutil.is_debug():
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
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug():
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
		if secret == SECRET_FASTSPRING or enki.libutil.is_debug():

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
				if enki.libutil.is_debug():
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
		                  active_page = 'store',
						  purchase_price = '$2.00',
						  purchaser_email = 'user_email@provided_to_Fastspring.com' ,
						  quantity = 2,
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ 'avoyd' ] )

	def post( self ):
		if not SECRET_FASTSPRING or enki.libutil.is_debug():

			product = 'product_name'
			quantity = xint( self.request.get('quantity'))
			purchase_price = xstr( self.request.get( 'purchase_price' ))
			purchaser_email = xstr( self.request.get( 'purchaser_email' ))
			license_keys = 'not generated'
			user_id = ''

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
			self.add_debugmessage( '<h1>Emulator - Store FastSpring</h1>'+
									'<h2>Emulated purchase details</h2>' +
									'<ul>' +
			                            '<li>quantity = ' + xstr( quantity ) + '</li>' +
			                            '<li>price = ' + purchase_price + '</li>' +
			                            '<li>email = ' + purchaser_email + '</li>' +
			                            '<li>license(s) = ' + xstr( license_keys ) + '</li>' +
									'</ul>'
									'<h2>Internal data</h2>' +
									'<ul>' +
			                            '<li>referrer = token purchasebyuser = ' + ( xstr( referrer ) if referrer else 'None' ) + '</li>' +
				                        '<li>purchaser user_id (if token purchasebyuser ) = ' + ( xstr( user_id ) if user_id else 'None' ) + '</li>' +
			                        '</ul>' )

			url = enki.libutil.get_local_url( 'ordercompletefastspring' )
			form_fields = { 'license_key' : license_keys,
			                'purchase_price' : purchase_price,
			                'order_id' : 'Emulator_order_id',
							'product_name' : product,
							'purchaser_email' : purchaser_email,
							'shop_name' : 'Emulator_FastSpring',
							'quantity' : quantity ,
			                'referrer' : referrer,
			                'is_test' : True }

			form_data = urllib.urlencode( form_fields )
			result = urlfetch.fetch( url = url, payload = form_data, method = urlfetch.POST )
			if result.status_code == 200:
				self.add_debugmessage( '<h2>Purchase records created<h2>' )
			else:
				self.add_debugmessage( '<h2>ERROR - purchase records not created<h2>' )

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
		data = []
		user_id = 6173208034148352
		data = enki.libstore.fetch_EnkiProuctKey_by_purchaser( user_id )
		return data


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' ),
		          webapp2.Route( '/genlicensefastspring', HandlerGenLicenseFastSpring, name = 'genlicensefastspring' ),
		          webapp2.Route( '/ordercompletefastspring', HandlerOrderCompleteFastSpring, name = 'ordercompletefastspring' ),
		          webapp2.Route( '/emulatestorefastspring', HandlerStoreEmulateFastSpring, name = 'storeemulatefastspring' ) ]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
