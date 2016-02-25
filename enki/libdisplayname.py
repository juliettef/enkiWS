import collections
import random
import re

from google.appengine.ext import ndb

import enki.libutil
from enki.modeldisplayname import EnkiModelDisplayName
from enki.modeluser import EnkiModelUser


entityList = collections.namedtuple( 'entity_list', 'entity, list' )
userDisplayNamePage = collections.namedtuple( 'user_display_name_page', 'user_id, display_name, user_page' )
displayNameSelection = collections.namedtuple( 'displayNameSelection', 'error, best_guess, suggestions')

DELETED_PREFIX = '[deleted]'
DELETED_SUFFIX = '#0000'

# 1 <= PREFIX_LENGTH_MIN < PREFIX_LENGTH_MAX
# longest syllable in prefix generator <= PREFIX_LENGTH_MAX
PREFIX_LENGTH_MAX = 12
PREFIX_LENGTH_MIN = 3

ERROR_DISPLAY_NAME_LENGTH = -41
ERROR_DISPLAY_NAME_ALNUM = -42
ERROR_DISPLAY_NAME_IN_USE = -43
ERROR_DISPLAY_NAME_INVALID = -44


def get_display_name( user_id ):
	# returns a user's full display name i.e. prefix + suffix from their user id
	display_name = ''
	entity = get_EnkiUserDisplayName_by_user_id_current( user_id )
	if entity:
		display_name = entity.prefix + entity.suffix
	return display_name


def get_user_id_from_display_name( display_name ):
	# return the user Id from a full display name
	prefix = display_name[ : -5 ]
	suffix = display_name[ -5: ]
	entity = get_EnkiUserDisplayName_by_prefix_suffix( prefix, suffix )
	return entity.user_id


def get_user_id_display_name_url( entity ):
	# based on a display name entity, return a named tuple containing their user_id, display name and url
	user_id = entity.user_id
	display_name = entity.prefix + entity.suffix
	user_page = enki.libutil.get_local_url( 'profilepublic', { 'useridnumber': str( user_id ) } )
	result = userDisplayNamePage( user_id , display_name, user_page )
	return result


def find_users_by_display_name( input_name, user_id ):
	# TODO: problem: the search is case insensitive on the prefix => if CCC#1234 and Ccc#1234 exist, requesting CCc#1234 will return 1 best guess only
	prefix = ''
	suffix = ''
	error = None
	best_guess = None
	suggestions = []
	# check whether the display name has a suffix in it. If so extract the presumed suffix and prefix.
	found_suffix = re.search( '\#[1-9][0-9]{3}', input_name )
	if found_suffix:
		prefix = input_name[ :found_suffix.start()]
		suffix = found_suffix.group( 0 )
		not_exact = input_name[ found_suffix.end(): ]   # check if there's extra text after the suffix
		if not(( PREFIX_LENGTH_MIN <= len( prefix ) <= PREFIX_LENGTH_MAX ) or prefix.isalnum()) or not_exact:
			error = ERROR_DISPLAY_NAME_INVALID
	# otherwise, if input_name is the right format, assume it's a prefix
	elif ( PREFIX_LENGTH_MIN <= len( input_name ) <= PREFIX_LENGTH_MAX ) and input_name.isalnum():
		prefix = input_name
	else:
		error = ERROR_DISPLAY_NAME_INVALID

	if not error:
		# return the display name suggestions
		# best guess: if there is a match for prefix + suffix
		suggested_items = fetch_EnkiUserDisplayName_by_prefix_lower_current_minus_user_id( prefix.lower( ), user_id )
		if suggested_items:
			for i, item in enumerate( suggested_items ):
				if suffix and item.suffix == suffix:
					best_guess = get_user_id_display_name_url( item )
				else:
					suggestions.append( get_user_id_display_name_url( item ))
		else:
			error = ERROR_DISPLAY_NAME_INVALID

	return displayNameSelection( error, best_guess, suggestions)


def cosmopompe():
# generates a display name prefix
	# syllables are used to generate display names. They must be alphanumeric (including accented characters).
	# 1 <= syllable length <= PREFIX_LENGTH_MAX
	syllables = [ 'Ga', 'Bu', 'Zo', 'Meu' ] # shadok syllables
	syl_len_shortest = len( min(( word for word in syllables if word ), key = len ))
	syl_nr_min = PREFIX_LENGTH_MIN / syl_len_shortest + ( 0 if PREFIX_LENGTH_MIN % syl_len_shortest == 0 else 1 )
	syl_nr_max = PREFIX_LENGTH_MAX / syl_len_shortest
	attempt_prefix = 0
	unique = False
	while not unique:
	# generate a new prefix + suffix combo until unique
		unique = True
		prefix = ''
		max_syllables = random.randint( syl_nr_min, syl_nr_max ) # variable number of syllables per word
		syllable_counter = 1
		while len( prefix ) < PREFIX_LENGTH_MIN:
			while syllable_counter <= max_syllables:
				prefix_test = prefix + syllables[ random.randint( 0, len( syllables ) - 1 )]
				if len( prefix_test ) <= PREFIX_LENGTH_MAX:
					prefix = prefix_test
				else:
					break
				syllable_counter += 1
		suffix = '#' + str( random.randint( 1000, 9999 ))
		attempt_suffix = 0
		while exist_EnkiUserDisplayName_by_prefix_suffix( prefix, suffix ) :
			suffix = '#' + str( random.randint( 1000, 9999 ))
			attempt_suffix += 1
			if attempt_suffix > 999:
				unique = False
				break
		attempt_prefix += 1
		if attempt_prefix > 99:
			unique = False
			break
		if unique:
			display_name_split = [ prefix, suffix ]
			return display_name_split


def set_display_name( user_id, prefix, suffix ):
	# get the current name
	old_display_name = get_EnkiUserDisplayName_by_user_id_current( user_id )
	# save the new name
	display_name = EnkiModelDisplayName( parent = ndb.Key( EnkiModelUser, user_id ), user_id = user_id, prefix = prefix, suffix = suffix )
	display_name.put()
	if old_display_name:
	# if the user already had a display name, and a new same was set, set the old name to not current
		old_display_name.current = False
		old_display_name.put()


def make_unique_and_set_display_name( user_id, prefix ):
	if (PREFIX_LENGTH_MIN <= len( prefix ) <= PREFIX_LENGTH_MAX):
		if prefix.isalnum():
			result = enki.libutil.ENKILIB_OK
			# get the current name
			old_display_name = get_EnkiUserDisplayName_by_user_id_current( user_id )

			# if the user has used the same prefix in the past, reuse it
			if exist_EnkiUserDisplayName_by_user_id_prefix( user_id, prefix ):
				display_name = get_EnkiUserDisplayName_by_user_id_prefix( user_id, prefix )
				if display_name != old_display_name: # swap the names
					old_display_name.current = False
					old_display_name.put()
					display_name.current = True
					display_name.put()
				return True
			else:
			# if the user has never used that prefix, generate a suffix so that the combo prefix + suffix is unique over all users
				suffix = '#' + str( random.randint( 1000, 9999 ))
				i = 0
				while exist_EnkiUserDisplayName_by_prefix_suffix( prefix, suffix ) :
					# generate a new suffix until the prefix + suffix combo is unique
					suffix = '#' + str( random.randint( 1000, 9999 ))
					i += 1
					if i > 99:
						result = ERROR_DISPLAY_NAME_IN_USE
						break
				if result == enki.libutil.ENKILIB_OK:
					set_display_name( user_id, prefix, suffix )
		else:
			result = ERROR_DISPLAY_NAME_ALNUM
	else:
		result = ERROR_DISPLAY_NAME_LENGTH
	return result


def get_display_name_data( user_id ):
	# Note: the data retrieved may be old or incomplete
	# see https://cloud.google.com/appengine/docs/python/datastore/structuring_for_strong_consistency
	entity, list, error, info = [], [], '', ''
	current_display_name = get_EnkiUserDisplayName_by_user_id_current( user_id )
	if current_display_name:
		entity = get_user_id_display_name_url( current_display_name )
	list = get_user_display_name_old( user_id )
	result = entityList( entity, list )
	return result


def get_user_display_name_old( user_id ):
	list = fetch_EnkiUserDisplayName_by_user_id_not_current( user_id )
	old_names = []
	for item in list:
		old_names.append( item.prefix + item.suffix )
	return old_names


#=== QUERIES ==================================================================


def get_EnkiUserDisplayName_by_user_id_current( user_id ):
	entity = EnkiModelDisplayName.query( EnkiModelDisplayName.current == True,
	                                     ancestor = ndb.Key( EnkiModelUser, user_id )).get()
	return entity


def fetch_EnkiUserDisplayName_by_prefix_lower_current_minus_user_id( prefix_lower, user_id ):
	list = EnkiModelDisplayName.query( ndb.AND( EnkiModelDisplayName.prefix_lower == prefix_lower,
	                                            EnkiModelDisplayName.current == True,
	                                            EnkiModelDisplayName.user_id != user_id, )).fetch()
	return list


def exist_EnkiUserDisplayName_by_user_id( user_id ):
	count = EnkiModelDisplayName.query( ancestor = ndb.Key( EnkiModelUser, user_id )).count( 1 )
	return count > 0


def exist_EnkiUserDisplayName_by_user_id_prefix( user_id, prefix ):
	count = EnkiModelDisplayName.query( EnkiModelDisplayName.prefix == prefix,
	                                    ancestor = ndb.Key( EnkiModelUser, user_id )).count( 1 )
	return count > 0


def get_EnkiUserDisplayName_by_user_id_prefix( user_id, prefix ):
	entity = EnkiModelDisplayName.query( EnkiModelDisplayName.prefix == prefix,
	                                     ancestor = ndb.Key( EnkiModelUser, user_id )).get()
	return entity


def get_EnkiUserDisplayName_by_prefix_suffix( prefix, suffix ):
	entity = EnkiModelDisplayName.query( EnkiModelDisplayName.prefix == prefix,
	                                     EnkiModelDisplayName.suffix == suffix ).get()
	return entity


def exist_EnkiUserDisplayName_by_prefix_suffix( prefix, suffix ):
	count = EnkiModelDisplayName.query( ndb.AND( EnkiModelDisplayName.prefix == prefix,
	                                             EnkiModelDisplayName.suffix == suffix )).count( 1 )
	return count > 0


def fetch_EnkiUserDisplayName_by_user_id( user_id ):
	list = EnkiModelDisplayName.query( ancestor = ndb.Key( EnkiModelUser, user_id ) ).fetch( keys_only = True )
	return list


def fetch_EnkiUserDisplayName_by_user_id_not_current( user_id ):
	list = EnkiModelDisplayName.query( EnkiModelDisplayName.current == False,
	                                   ancestor = ndb.Key( EnkiModelUser, user_id ) ).fetch()
	return list
