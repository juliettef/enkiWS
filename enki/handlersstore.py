import webapp2

from webapp2_extras.i18n import gettext as _

import enki
import enki.libstore
from enki.modelproductkey import EnkiModelProductKey
from enki.extensions import Extension
from enki.extensions import ExtensionPage


products = { 'avoyd': { 'name' : 'Avoyd', 'price' : 3.00 },
             'avoyd-1999' : { 'name' : 'Avoyd-1999', 'price' : 0.00 },
             }


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		product = products[ 'avoyd' ]
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  CSRFtoken = self.create_CSRF( 'store' ),
		                  product = product )

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


class ExtensionPageProducts( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'store', template_include = 'incproducts.html' )

	def get_data( self, handler ):
		data = [ 'Game1', 'Game2', 'Music1', 'Music2', 'Music3', 'Art1', 'Art2' ]
		return data


class ExtensionStore( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/store', HandlerStore, name = 'store' )]

	def get_navbar_items( self ):
		return [( enki.libutil.get_local_url( 'store' ), 'store', _( "Store" ))]

	def get_page_extensions( self ):
		return [ ExtensionPageProducts()]
