import enki.jinjafilters
import enki.handlersoauth
import enki.modelforum
import enki.libutil


ENKI_FORCE_DEBUG = False    # If True, behaves as if it's offline
ENKI_EMULATE_STORE = True  # If True, use the store emulator

REAUTH_EXPIRY = 5  # minutes

LOCALES = [ 'en_US', 'en_EN', 'fr_FR' ]


product_displayname = { 'product_a' : 'Product A',
                        'product_b' : 'Product B',
                        'product_c' : 'Product C',
                        'product_d' : 'Product D', }

COMPANY_NAME = "Company"


# lists of user roles and permissions
ROLES = { 'RUC':'User, Confirmed',
		  'RFM':'Forum Moderator', }
PERMISSIONS = { 'PFTS' :'Permission to set/unset Forum Thread Sticky',
				'PFPS' : 'Permission to set/unset Forum Post Sticky', }
# permissions granted to each role
ROLES_PERMISSIONS = { 'RUC' : [],
					  'RFM' : [ 'PFTS', 'PFPS' ], }


# admin email notifications
ADMIN_EMAIL_ADDRESSES = { 'admin1@enkiWS.com': [ 'FPD' ]}
ADMIN_EMAIL_TYPES = { 'FTPA' : 'Forum Thread and Post added',
					  'FPA' : 'Forum Post added',
					  'FPE' : 'Forum Post edited',
					  'FPD' : 'Forum Post deleted' }
ADMIN_EMAIL_SUBJECT_PREFIX = '[ enkiWS admin ] '


# Forums groups and groups' topics (ordered)
FORUMS = [[ 'Group A', 'Title A-1', 'Description A-1' ],
		  [ 'Group A', 'Title A-2', 'Description A-2' ],
		  [ 'Group A', 'Title A-3', 'Description A-3' ],
		  [ 'Group B', 'Title B-1', 'Description B-1' ],
		  [ 'Group B', 'Title B-2', 'Description B-2' ],
		  ]


CANONICAL_HOST_URL = ( '' if enki.libutil.is_develop_server() else '' )
#e.g. CANONICAL_HOST_URL = ( '' if enki.libutil.is_debug() else 'https://www.enkisoftware.com' )
# note no trailing slash

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
config[ 'webapp2_extras.sessions' ] = { 'secret_key': KEY_SESSION,
										'session_max_age': 3600,
										'cookie_args': { 'max_age' : None,
														 'domain' : None,
														 'secure' : ( None if enki.libutil.is_debug() else True ),
														 'httponly' : True, 'path' : '/' }
										}
config[ 'webapp2_extras.jinja2' ] = { 'template_path': 'templates',
                                      'environment_args': { 'extensions': [ 'jinja2.ext.i18n' ]},
                                      'filters': { 'local' : enki.jinjafilters.make_local_url,
                                                   'joinurl' : enki.jinjafilters.join_url_param_char,
												   'changelocale' : enki.jinjafilters.change_locale_url }
                                      }
