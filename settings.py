import enki.jinjafilters
import enki.handlersoauth
import enki.modelforum


ENKI_FORCE_DEBUG = False    # If True, behaves as if it's offline
ENKI_EMULATE_STORE = True  # If True, use the store emulator

REAUTH_EXPIRY = 5  # minutes

LOCALES = [ 'en_US', 'en_EN', 'fr_FR' ]


product_displayname = { 'product_a' : 'Product A',
                        'product_b' : 'Product B',
                        'product_c' : 'Product C',
                        'product_d' : 'Product D', }

COMPANY_NAME = "Company"


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
	URL_PURCHASE_FASTSPRING = secrets.URL_PURCHASE_FASTSPRING
	SECRET_FASTSPRING = secrets.SECRET_FASTSPRING
	URLS_ENKIDL = secrets.URLS_ENKIDL
	SECRET_ENKIDL = secrets.SECRET_ENKIDL
	SECRET_API_KEY_MAILGUN = secrets.SECRET_API_KEY_MAILGUN
	SECRETS_EXIST = True
	if secrets.CLIENT_ID_GOOGLE:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthGoogle ]
	if secrets.CLIENT_ID_FACEBOOK:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthFacebook ]
	if secrets.CLIENT_ID_GITHUB:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthGithub ]
	if secrets.CLIENT_ID_TWITTER:
		HANDLERS += [ enki.handlersoauth.HandlerOAuthTwitter ]
except ImportError:
	KEY_SESSION = 'See example_secrets.txt'
	URL_PURCHASE_FASTSPRING = ''
	SECRET_FASTSPRING = ''
	URLS_ENKIDL = ''
	SECRET_ENKIDL = ''
	SECRET_API_KEY_MAILGUN = ''
	SECRETS_EXIST = False
	pass


def get_routes_oauth( ):
	routes_oauth = []
	for handler in HANDLERS:
		routes_oauth += handler.get_routes( )
	return routes_oauth


config = {}
config[ 'enki' ] = { 'user' : { 'PASSWORD_LENGTH_MIN' : 4 }
                     }
config[ 'webapp2_extras.sessions' ] = { 'secret_key': KEY_SESSION }
config[ 'webapp2_extras.jinja2' ] = { 'template_path': 'templates',
                                      'environment_args': { 'extensions': [ 'jinja2.ext.i18n' ]},
                                      'filters': { 'local' : enki.jinjafilters.make_local_url,
                                                   'joinurl' : enki.jinjafilters.join_url_param_char,
												   'changelocale' : enki.jinjafilters.change_locale_url }
                                      }
