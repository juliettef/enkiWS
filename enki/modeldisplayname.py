import collections
import random
import re

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model

import enki.libutil

from enki.modeluser import EnkiModelUser


entityList = collections.namedtuple( 'entity_list', 'entity, list' )
userDisplayNamePage = collections.namedtuple( 'user_display_name_page', 'user_id, display_name, user_page' )
displayNameSelection = collections.namedtuple( 'displayNameSelection', 'error, best_match, suggestions')


class EnkiModelDisplayName( model.Model ):

	#=== MODEL ====================================================================

	user_id = model.IntegerProperty()
	prefix = model.StringProperty() # prefix e.g. 'Jane'
	prefix_lower = model.ComputedProperty(lambda self: self.prefix.lower()) # lowercase prefix e.g. "jane"
	suffix = model.StringProperty() # suffix e.g. '#1234' => full display name = 'Jane#1234'
	current = model.BooleanProperty( default = True )
	time_created = model.DateTimeProperty( auto_now_add = True )

	#=== CONSTANTS ================================================================

	DELETED_PREFIX = '[deleted]'
	DELETED_SUFFIX = '#0000'

	# 1 <= PREFIX_LENGTH_MIN < PREFIX_LENGTH_MAX
	# longest syllable in prefix generator <= PREFIX_LENGTH_MAX
	PREFIX_LENGTH_MAX = 12
	PREFIX_LENGTH_MIN = 3
	DISPLAY_NAME_LENGTH_MAX = PREFIX_LENGTH_MAX + 5     # prefix + suffix, suffix = '#' + 4 digits

	ERROR_DISPLAY_NAME_LENGTH = -41
	ERROR_DISPLAY_NAME_ALNUM = -42
	ERROR_DISPLAY_NAME_IN_USE = -43
	ERROR_DISPLAY_NAME_INVALID = -44
	ERROR_DISPLAY_NAME_NOT_EXIST = -45

	#=== QUERIES ==================================================================

	@classmethod
	def exist_by_user_id( cls, user_id ):
		count = cls.query( ancestor = ndb.Key( EnkiModelUser, user_id )).count( 1 )
		return count > 0

	@classmethod
	def get_by_user_id_current( cls, user_id ):
		return cls.query( cls.current == True, ancestor = ndb.Key( EnkiModelUser, user_id )).get()

	@classmethod
	def fetch_by_prefix_lower_current( cls, prefix_lower ):
		return cls.query( ndb.AND( cls.prefix_lower == prefix_lower, cls.current == True )).fetch()

	@classmethod
	def exist_by_user_id_prefix_lower( cls, user_id, prefix_lower ):#exist_EnkiUserDisplayName_by_user_id_prefix_lower # TODO delete?
		count = cls.query( cls.prefix_lower == prefix_lower, ancestor = ndb.Key( EnkiModelUser, user_id )).count( 1 )
		return count > 0

	@classmethod
	def get_by_user_id_prefix_lower( cls, user_id, prefix_lower ):
		return cls.query( cls.prefix_lower == prefix_lower, ancestor = ndb.Key( EnkiModelUser, user_id )).get()

	@classmethod
	def exist_by_prefix_lower_suffix( cls, prefix_lower, suffix ):
		count = cls.query( ndb.AND( cls.prefix_lower == prefix_lower, cls.suffix == suffix )).count( 1 )
		return count > 0

	@classmethod
	def get_by_prefix_lower_suffix( cls, prefix_lower, suffix ):
		return cls.query( cls.prefix_lower == prefix_lower, cls.suffix == suffix ).get()

	@classmethod
	def fetch_keys_by_user_id( cls, user_id ):
		return cls.query( ancestor = ndb.Key( EnkiModelUser, user_id )).fetch( keys_only = True )

	@classmethod
	def fetch_by_user_id_not_current( cls, user_id ):
		return cls.query( cls.current == False, ancestor = ndb.Key( EnkiModelUser, user_id )).fetch()

	@classmethod
	def count_current( cls ):
		return cls.query( cls.current == True ).count()

	#=== UTILITIES ================================================================

	@classmethod
	def get_display_name( cls, user_id ):
		# returns a user's full display name i.e. prefix + suffix from their user id
		display_name = ''
		entity = cls.get_by_user_id_current( user_id )
		if entity:
			display_name = entity.prefix + entity.suffix
		return display_name

	@classmethod
	def get_user_id_from_display_name( cls, display_name ):
		# return the user Id from a full display name
		prefix = display_name[ : -5 ]
		suffix = display_name[ -5: ]
		entity = cls.get_by_prefix_lower_suffix( prefix.lower(), suffix )
		return entity.user_id

	@classmethod
	def get_user_id_display_name_url( cls, entity ):
		# based on a display name entity, return a named tuple containing their user_id, display name and url
		user_id = entity.user_id
		display_name = entity.prefix + entity.suffix
		user_page = enki.libutil.get_local_url( 'profilepublic', { 'useridnumber': str( user_id ) } )
		result = userDisplayNamePage( user_id , display_name, user_page )
		return result

	@classmethod
	def get_user_id_display_name( cls, entity ):
		# based on a display name entity, returns a dictionary containing their user_id and display name
		user_id = str( entity.user_id )
		display_name = str( entity.prefix + entity.suffix )
		result = { 'user_id' : user_id, 'displayname' : display_name }
		return result

	@classmethod
	def find_users_by_display_name( cls, display_name, user_ids_to_ignore = []):
		prefix = ''
		suffix = ''
		error = None
		best_match = None
		suggestions = []

		# check whether the display name has a suffix in it. If so extract the presumed suffix and prefix.
		found_suffix = re.search( '\#[1-9][0-9]{3}', display_name )
		if found_suffix:
			prefix = display_name[ :found_suffix.start( ) ]
			suffix = found_suffix.group( 0 )
			if not(( cls.PREFIX_LENGTH_MIN <= len( prefix ) <= cls.PREFIX_LENGTH_MAX ) or prefix.isalnum()):
				error = cls.ERROR_DISPLAY_NAME_INVALID
		# otherwise, if display_name is the right format, assume it's a prefix
		elif ( cls.PREFIX_LENGTH_MIN <= len( display_name ) <= cls.PREFIX_LENGTH_MAX ) and display_name.isalnum():
			prefix = display_name
		else:
			error = cls.ERROR_DISPLAY_NAME_INVALID

		if not error:
			# return the display name suggestions
			# best guess: if there is a match for prefix + suffix
			suggested_items = cls.fetch_by_prefix_lower_current( prefix.lower())
			if suggested_items:
				for i, item in enumerate( suggested_items ):
					if item.user_id not in user_ids_to_ignore:
						if suffix and item.suffix == suffix:
							best_match = cls.get_user_id_display_name_url( item )
						else:
							suggestions.append( cls.get_user_id_display_name_url( item ))
				if not best_match and not suggestions:
					error = cls.ERROR_DISPLAY_NAME_NOT_EXIST
			else:
				error = cls.ERROR_DISPLAY_NAME_NOT_EXIST

		return displayNameSelection( error, best_match, suggestions)

	@classmethod
	def cosmopompe( cls ):
		# Generate a display name
		# About the Shadok word generator: https://www.enkisoftware.com/devlogpost-20190405-1
		syllables = [ 'Ga', 'Bu', 'Zo', 'Meu' ] # shadok syllables (alphanumeric, can include accented characters).
		min_syllables = cls.PREFIX_LENGTH_MIN / 3	# minimum prefix length / longest syllable length
		max_syllables = cls.PREFIX_LENGTH_MAX / 2
		# attempt to generate a unique combo [ prefix, suffix ]. Stop after an arbitrary number of attempts.
		attempt = 0
		while attempt < 99:
			# generate a prefix
			prefix = ''
			num_syllables = random.randint( min_syllables, max_syllables )
			count_syllables = 0
			while count_syllables < num_syllables or len( prefix ) < cls.PREFIX_LENGTH_MIN:
				syllable = random.choice( syllables )
				if ( len( prefix + syllable ) > cls.PREFIX_LENGTH_MAX ):
					break  # abort if the predicted prefix is too long
				prefix += syllable
				count_syllables += 1
			# if the resulting combination already exists, try new suffixes until reach a unique combo. Stop after x attemps.
			attempt_suffix = 0
			while attempt_suffix < 99:
				# generate a suffix
				suffix = '#' + str( random.randint( 1000, 9999 ))
				if cls.exist_by_prefix_lower_suffix( prefix.lower(), suffix ):
					attempt_suffix += 1
				else:
					return [ prefix, suffix ]
			attempt += 1
		return [0]	# display name generation failed

	@classmethod
	def set_display_name( cls, user_id, prefix, suffix ):
		# get the current name
		old_display_name = cls.get_by_user_id_current( user_id )
		# save the new name
		display_name = EnkiModelDisplayName( parent = ndb.Key( EnkiModelUser, user_id ), user_id = user_id, prefix = prefix, suffix = suffix )
		display_name.put()
		if old_display_name:
		# if the user already had a display name, and a new same was set, set the old name to not current
			old_display_name.current = False
			old_display_name.put()

	@classmethod
	def make_unique_and_set_display_name( cls, user_id, prefix ):
		if ( cls.PREFIX_LENGTH_MIN <= len( prefix ) <= cls.PREFIX_LENGTH_MAX ):
			if prefix.isalnum():
				result = enki.libutil.ENKILIB_OK
				# get the current name
				display_name_current = cls.get_by_user_id_current( user_id )
				# if the user has used the same prefix in the past, reuse it
				display_name_old = cls.get_by_user_id_prefix_lower( user_id, prefix.lower())
				if display_name_current and display_name_old:
					if display_name_current != display_name_old:
						# swap the names
						display_name_current.current = False
						display_name_current.put()
						display_name_old.prefix = prefix   # update the mixed case prefix in case it has changed
						display_name_old.current = True
						display_name_old.put()
					elif display_name_current.prefix != prefix:
						# update the mixed case prefix of the current name
						display_name_current.prefix = prefix
						display_name_current.put()
					return True
				else:
				# if the user has never used that prefix, generate a suffix so that the combo lowercase prefix + suffix is unique over all users
					suffix = '#' + str( random.randint( 1000, 9999 ))
					i = 0
					while cls.exist_by_prefix_lower_suffix( prefix.lower(), suffix ) :
						# generate a new suffix until the prefix + suffix combo is unique
						suffix = '#' + str( random.randint( 1000, 9999 ))
						i += 1
						if i > 99:
							result = cls.ERROR_DISPLAY_NAME_IN_USE
							break
					if result == enki.libutil.ENKILIB_OK:
						cls.set_display_name( user_id, prefix, suffix )
			else:
				result = cls.ERROR_DISPLAY_NAME_ALNUM
		else:
			result = cls.ERROR_DISPLAY_NAME_LENGTH
		return result

	@classmethod
	def get_display_name_data( cls, user_id ):
		# Note: the data retrieved may be old or incomplete
		# see https://cloud.google.com/appengine/docs/python/datastore/structuring_for_strong_consistency
		entity, list, error, info = [], [], '', ''
		current_display_name = cls.get_by_user_id_current( user_id )
		if current_display_name:
			entity = cls.get_user_id_display_name_url( current_display_name )
		list = cls.get_user_display_name_old( user_id )
		result = entityList( entity, list )
		return result

	@classmethod
	def get_user_display_name_old( cls, user_id ):
		list = cls.fetch_by_user_id_not_current( user_id )
		old_names = []
		for item in list:
			old_names.append( item.prefix + item.suffix )
		return old_names
