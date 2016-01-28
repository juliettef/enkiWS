import webapp2

from webapp2_extras.i18n import gettext as _

import enki
import enki.libstore
import enki.textmessages as MSG
from enki.modelproductkey import EnkiModelProductKey
from enki.extensions import Extension
from enki.extensions import ExtensionPage


products = { 'avoyd': { 'displayname' : 'Avoyd', 'price' : 3.00 },
             'avoyd-1999' : { 'displayname' : 'Avoyd-1999', 'price' : 0.00 },
             }


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ 'avoyd' ] )

	def post( self ):
		self.check_CSRF( 'store' )
		product_code = enki.libstore.generate_product_code()
		product = 'avoyd'
		purchaser_email = ''
		purchaser_user_id = None
		if self.is_logged_in():
			purchaser_email = self.enki_user.email
			purchaser_user_id = self.enki_user.key.id()
		item = EnkiModelProductKey( product_code = product_code,
		                            product_name = product,
		                            purchaser_email = purchaser_email,
		                            purchaser_user_id = purchaser_user_id,
		                            purchase_price = float( products[ product ][ 'price' ]),
		                            )
		EnkiModelProductKey.put( item )
		product_name = products[ product ][ 'displayname' ]
		product_code_formatted = enki.libstore.insert_dash_5_10( product_code.encode( 'utf-8' ) )
		link_product_code = enki.libutil.get_local_url( 'profile', { 'code' : product_code_formatted })
		if purchaser_email: # TODO: get email address
			self.send_email( purchaser_email, MSG.SEND_EMAIL_PRODUCT_OWN_SUBJECT( product_name ),
			                 MSG.SEND_EMAIL_PRODUCT_OWN_BODY( product = product_name,
			                                                  code = product_code_formatted,
			                                                  link = link_product_code ))
		self.add_infomessage( 'success', MSG.SUCCESS(), MSG.PRODUCT_OWNED(  product = product_name,
			                                                                code = product_code_formatted,
			                                                                link = link_product_code ))
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = products[ product ])

#TODO: 1. [DONE] Add POST render of success page.
#TODO: 2. Add a page extension to the profile (not public) which lists your products you have purchased, and their status (registered or not).
#TODO: 3. Add a way to register a product you own.
#TODO: 4. Add a way to register any product from a key.


class HandlerGenLicenseFastSpring( enki.HandlerBase ):

	def post( self ):
		quantity = self.request.get( 'quantity' )
		product_codes = ''
		if quantity:
			quantity = int( quantity )
			while quantity > 0:
				product_codes += enki.libstore.insert_dash_5_10( enki.libstore.generate_product_code()) + '\n'
				quantity -= 1
			self.response.write( product_codes )
			return
		self.abort( 404 )


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
#		user  = self.enki_user.key.id()
		user_id = 6173208034148352
		data = enki.libstore.fetch_EnkiProuctKey_by_purchaser( user_id )
		return data


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' ),
		          webapp2.Route( '/genlicensefastspring', HandlerGenLicenseFastSpring, name = 'genlicensefastspring'  )]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts(), ExtensionPageLibrary()]
