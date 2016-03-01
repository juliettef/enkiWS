class ExtensionPage():

	def __init__( self, route_name, template_include ):
		self.route_name = route_name
		self.template_include = template_include

	def get_data( self, handler ):
		return None


class Extension():

	def get_routes( self ):
		return []

	def get_navbar_items( self ):
		return[]

	def get_page_extensions( self ):
		return []


class ExtensionLibrary():

	extensions = []
	dict_page_extensions = {}

	@classmethod
	def set_extensions( cls, extensionlist ):
		cls.extensions = extensionlist
		for extension in cls.extensions:
			page_extensions = extension.get_page_extensions()
			for page_extension in page_extensions:
				if cls.dict_page_extensions.get( page_extension.route_name ):
					cls.dict_page_extensions[ page_extension.route_name ] += [ page_extension ]
				else:
					cls.dict_page_extensions[ page_extension.route_name ] = [ page_extension ]

	@classmethod
	def get_routes( cls ):
		routes = []
		for extension in cls.extensions:
			routes += extension.get_routes()
		return routes

	@classmethod
	def get_navbar_items( cls ):
		items = []
		for extension in cls.extensions:
			items += extension.get_navbar_items()
		return items

	@classmethod
	def get_page_extensions_route( cls, handler, route_name ):
		list_data = []
		page_extensions = cls.dict_page_extensions.get( route_name )
		if page_extensions:
			for page_extension in page_extensions:
				data = page_extension.get_data( handler )
				list_data += [( page_extension.template_include, data )]
		return list_data

	@classmethod
	def get_page_extensions( cls, handler ):
		return cls.get_page_extensions_route( handler, handler.request.route.name )

	@classmethod
	def get_navbar_extensions( cls, handler ):
		return cls.get_page_extensions_route( 'navbar' )
