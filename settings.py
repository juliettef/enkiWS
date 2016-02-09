import enki.handlersoauth
import enki.modelforum


ENKI_FORCE_DEBUG = False    # If True, behaves as if it's offline
ENKI_EMULATE_STORE = True  # If True, use the store emulator


URL_PURCHASE_FASTSPRING = str( 'https://sites.fastspring.com/enkisoftware/product/avoyd' )


product_displayname = { 'product_a' : 'Product A',
                        'product_b' : 'Product B',  }


def get_forum_default_topics():
	forum_topics = [
		enki.modelforum.EnkiModelForum( group = 'Company', order = 10, title = 'General', description = 'General discussion' ),
		enki.modelforum.EnkiModelForum( group = 'Company', order = 20, title = 'News', description = 'Latest news' ),
		enki.modelforum.EnkiModelForum( group = 'Company', order = 30, title = 'Support', description = 'Questions, feedback and bug reports' ),
        enki.modelforum.EnkiModelForum( group = 'Game', order = 10, title = 'General', description = 'General discussion' ),
		enki.modelforum.EnkiModelForum( group = 'Game', order = 20, title = 'News', description = 'Latest news' ),
		enki.modelforum.EnkiModelForum( group = 'Game', order = 30, title = 'Support', description = 'Questions, feedback and bug reports' ),
		]
	return forum_topics


# Steam OAuth always available as it doesn't use client ID nor secret - as of Jan 2016
HANDLERS = [ enki.handlersoauth.HandlerOAuthSteam ]


try:
	from secrets import secrets
	KEY_SESSION = secrets.KEY_SESSION
	SECRET_FASTSPRING = secrets.SECRET_FASTSPRING
	SECRETS_EXIST = True
	if secrets.CLIENT_ID_GOOGLE:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthGoogle ]
	if secrets.CLIENT_ID_FACEBOOK:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthFacebook ]
	if secrets.CLIENT_ID_TWITTER:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthTwitter ]
except ImportError:
	KEY_SESSION = 'See example_secrets.txt'
	SECRET_FASTSPRING = ''
	SECRETS_EXIST = False
	pass


def get_routes_oauth( ):
	routes_oauth = []
	for handler in HANDLERS:
		routes_oauth += handler.get_routes( )
	return routes_oauth
