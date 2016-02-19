import webapp2

import settings
import enki
import enki.textmessages as MSG


class HandlerMain( enki.HandlerBase ):

	def get(self):
		if not settings.SECRETS_EXIST:
			self.add_infomessage( 'warning', MSG.WARNING(), 'Setup incomplete, see <a class="alert-link"" href="https://github.com/juliettef/enkiWS#enabling-oauth-login-with-google-facebook-twitter">documentation</a>.')
		self.render_tmpl( 'home.html', False,
		                  active_menu = 'home' )

enki.ExtensionLibrary.set_extensions([ enki.ExtensionStore(),
                                       enki.ExtensionForums(),
                                       enki.ExtensionRestAPI(),
                                       enki.ExtensionFriends(),
                                       ])

config = {}
config[ 'webapp2_extras.sessions' ] = { 'secret_key': settings.KEY_SESSION }
config[ 'webapp2_extras.jinja2' ] = { 'template_path': 'templates',
                                      'environment_args': { 'extensions': [ 'jinja2.ext.i18n' ]},
                                      'filters': { 'local' : enki.jinjafilters.make_local_url,
                                                   'joinurl' : enki.jinjafilters.join_url_param_char }
                                      }


routes = [ webapp2.Route( '/', HandlerMain, name = 'home' ) ]
routes += enki.routes_account \
          + settings.get_routes_oauth() \
          + enki.ExtensionLibrary.get_routes()


app = webapp2.WSGIApplication( routes = routes, debug = enki.libutil.is_debug(), config = config )
