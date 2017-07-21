import urlparse
import jinja2

import enki.libutil


@jinja2.contextfilter
def make_local_url( context, route_name = 'home', parameters = {} ):
	return enki.libutil.make_local_url( context[ 'locale' ], route_name, parameters )

@jinja2.contextfilter
def change_locale_url( context, input_url, input_locale = '' ):
	output_url = input_url
	curr_locale = context[ 'locale' ]
	# add or modify parameters in a url
	if input_locale or curr_locale:
		# replace the parameter values of the url with the corresponding values in the dictionary
		# parse the input url
		parsed_url = urlparse.urlparse(output_url)
		parsed_url_list = list(parsed_url)
		output_path = enki.libutil.strip_locale_from_path( parsed_url.path, curr_locale )
		if input_locale:
			output_path = '/' + input_locale + output_path
		parsed_url_list[2] = output_path
		# build the new url with the updated parameters
		output_url = urlparse.urlunparse(parsed_url_list)
	return output_url

def join_url_param_char( input_url, parameters = {}):
	output_url = input_url
	# add or modify parameters in a url
	if parameters:
		# replace the parameter values of the url with the corresponding values in the dictionary
		# parse the input url
		parsed_url= urlparse.urlparse( output_url )
		# if the original url had a query, update it with the input parameters
		parsed_url_query = {}
		if parsed_url.query:
			parsed_url_query = dict( urlparse.parse_qsl( parsed_url.query, keep_blank_values = True )) # note: can't handle multiple values for the same key
		parsed_url_query.update( parameters )
		# turn the parsed url result into a list, update it with the new query parameters (encoded)
		parsed_url_list = list( parsed_url )
		parsed_url_list[ 4 ] = enki.libutil.urlencode( parsed_url_query )
		# build the new url with the updated parameters
		output_url = urlparse.urlunparse( parsed_url_list )
	return output_url
