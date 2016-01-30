import webapp2

from webapp2_extras import security
from webapp2_extras.i18n import gettext as _

import enki
import enki.libstore
import enki.libuser
import enki.textmessages as MSG
from enki.modelproductkey import EnkiModelProductKey
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.extensions import Extension
from enki.extensions import ExtensionPage



products = { 'avoyd': { 'displayname' : 'Avoyd', 'price' : 3.00 },
             'avoyd-1999' : { 'displayname' : 'Avoyd-1999', 'price' : 0.00 },
             }

SECRET_FASTSPRING = '67Rbc2TphwLw8DGfmstdVmsx' # TODO: move to secrets
SEPARATOR_LICENSE_KEY_FASTSPRING = '\n'
URL_PURCHASE_FASTSPRING = str( 'https://sites.fastspring.com/enkisoftware/product/avoyd' )

class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ 'avoyd' ] )

	def post( self ):
		self.check_CSRF( 'store' )
		url_purchase = URL_PURCHASE_FASTSPRING
		if self.is_logged_in():
			purchaser_user_id = self.enki_user.key.id()
			token = security.generate_random_string( entropy = 256 )
			token_purchase = EnkiModelTokenVerify( token = token, user_id = purchaser_user_id, type = 'purchasebyuser' )
			token_purchase.put()
			url_purchase += str( '?referrer=' + token_purchase.token )
		self.redirect( url_purchase )


#TODO: 1. [DONE] Add POST render of success page.
#TODO: 2. Add a page extension to the profile (not public) which lists your products you have purchased, and their status (registered or not).
#TODO: 3. Add a way to register a product you own.
#TODO: 4. Add a way to register any product from a key.
#TODO: 5. [DONE] Security key for FastSpring


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
		if secret == SECRET_FASTSPRING:

			quantity = xint( self.request.get( 'quantity' ))
			license_keys = ''
			if quantity:
				quantity = int( quantity )
				while quantity > 0:
					license_keys += enki.libstore.insert_dash_5_10( enki.libstore.generate_license_key( ) ) \
					                + SEPARATOR_LICENSE_KEY_FASTSPRING
					quantity -= 1
				self.response.write( license_keys )
				return
		self.abort( 404 )


class HandlerOrderCompleteFastSpring( webapp2.RequestHandler ):

	def get(self):
		self.post()

	def post( self ):
		secret = xstr( self.request.get( 'secret' ))
		if secret == SECRET_FASTSPRING:

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

			license_keys = [ license_key_bundle.rstrip( SEPARATOR_LICENSE_KEY_FASTSPRING ) ]
			if (SEPARATOR_LICENSE_KEY_FASTSPRING) in license_key_bundle:
				# split the bundled license keys and create a record for each
				license_keys = license_key_bundle.split( SEPARATOR_LICENSE_KEY_FASTSPRING )
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
		          webapp2.Route( '/ordercompletefastspring', HandlerOrderCompleteFastSpring, name = 'ordercompletefastspring' )]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
