import webapp2

from webapp2_extras.i18n import gettext as _

import enki
from enki.modelproductkey import EnkiModelProductKey
from enki.extensions import Extension
from enki.extensions import ExtensionPage


class HandlerStore( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'store.html',
		                  active_page = 'store',
		                  product = 'Avoyd')

	def post( self ):
		product = 'Avoyd'
		item = EnkiModelProductKey( product_name = product )
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
