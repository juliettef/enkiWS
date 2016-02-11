# Note: messages are functions - instead of variables - so that they are extracted by Babel for translation.

from webapp2_extras.i18n import gettext as _
from webapp2_extras.i18n import ngettext


def SUCCESS(): return _( "Success" )
def INFORMATION(): return _( "Information" )
def WARNING(): return _( "Warning" )

def LOGGED_OUT(): return _( "You are logged out." )
def LOGIN_NEEDED(): return _( "Please log in to access the page you requested." )
def LOGGED_IN(): return _( "You are logged in." )

def REGISTRATION_ABORT(): return _( "Sign up aborted." )
def REGISTRATION_INFO_EMAIL_SENT( email ): return _( "If email address %(email)s is available, a registration email was sent to it. Please check your inbox and follow the instructions in the email to <b>confirm your registration</b>.", email = email )
def ACCOUNT_CREATED(): return _( "Your account is created." )

def AUTH_LOGIN_FAILED( provider_name ): return _( "Login with %(provider)s failed, please try again.", provider = provider_name )
def REGISTER_AUTH_ADD_EMAIL_INFO_EMAIL_SENT( email ): return _( "If email address %(email)s is available, an email was sent to it. Please check your inbox and follow the instructions in the email to <b>add it to your account</b>.", email = email )

def ACCOUNT_DELETED(): return _( "Your account is deleted." )
def ACCOUNT_DELETE_INFO_EMAIL_SENT( email ): return _( "An email was sent to your email address %(email)s. Please check your inbox and follow the instructions in the email to delete your account.", email = email )
def ACCOUNT_AND_POSTS_DELETED(): return _( "Your account and forum posts are deleted" )
def ACCOUNT_AND_POSTS_DELETE_INFO_EMAIL_SENT( email ): return _( "An email was sent to your email address %(email)s. Please check your inbox and follow the instructions in the email to delete your account and forum posts.", email = email )

def EMAIL_SET(): return _( "Your email address is set." )
def EMAIL_REMOVED(): return _( "Your email is removed." )
def EMAIL_RESTORED(): return _( "Your email address is restored." )
def EMAIL_ROLLBACK_INFO_EMAIL_SENT(): return _( "An email was sent to your previous address in case you want to <b>undo</b> the change." )
def EMAIL_CHANGE_CONFIRM_INFO_EMAIL_SENT( email ): return _( "If email address %(email)s is available, an email was sent to it. Please check your inbox and follow the instructions in the message to <b>confirm</b> the change.", email = email )
def EMAIL_CHANGE_UNDO_INFO_EMAIL_SENT(): return _( "An email was sent to your current address in case you want to <b>undo</b> the change." )

def AUTH_METHOD_REMOVED( provider_name ): return _( "%(provider)s authentication method removed.", provider = provider_name )

def PASSWORD_UPDATED(): return _( "Your password is updated." )
def PASSWORD_SET(): return _( "Your password is set." )
def PASSWORD_RESET_INFO_EMAIL_SENT( email ): return _( "If email address %(email)s matches an existing account, an email was sent to it. Please check your inbox and follow the instructions in the email to reset you password.", email = email )

def DISPLAYNAME_NEEDED(): return _( "Please set your display name to continue." )
def DISPLAYNAME_SET(): return _( "Your display name is set." )

def THREAD_PUBLISHED(): return _( "Your thread is published." )
def POST_PUBLISHED(): return _( "Your post is published." )
def POST_MODIFIED(): return _( "Your post is modified." )
def POST_DELETED(): return _( "Your post is deleted." )

def PRODUCT_OWNED( product, code, link ): return _( '''Congratulations, you own <b>%(product)s</b>. The product key is <b>%(code)s</b>. Check your email or <a href="%(link)s" class="alert-link">visit this page to activate it</a>.''', product = product, code = code, link = link )

# error messages
def WRONG_EMAIL_OR_PW(): return _( "Wrong email or password." )
def WRONG_PW(): return _( "Invalid password." )
def BACKOFF_LOGIN( timeout ): return _( "You have attempted to log in too many times. Please wait %(timeout)s before you try again.", timeout = timeout )
def BACKOFF_LICENCE( timeout ): return _( "You have attempted to activate a licence too many times. Please wait %(timeout)s before you try again.", timeout = timeout )
def WRONG_EMAIL_FORMAT(): return _( "Invalid email address format." )
def MISSING_EMAIL(): return _( "An email address is needed." )
def MISSING_PW(): return _( "A password is needed." )
def MISSING_NEW_PW(): return _( "Please enter your new password." )
def FAIL_REGISTRATION(): return _( "User creation failed, please retry." )
def PW_TOO_SHORT( length ): return ngettext( "Your password is %(length)s character long: it is too short.", "Your password is %(length)s characters long: it is too short.", length, length = length )
def PW_ENSURE_MIN_LENGTH( length ): return ngettext( "Please ensure your password is at least %(length)s character long.", "Please ensure your password is at least %(length)s characters long.", length, length = length)
def CURRENT_EMAIL(): return _( "This is your current email." )
def CANNOT_DELETE_EMAIL(): return _( "You cannot delete your email address: you need an email address to connect to your account." )

def UNIT_SECOND( nr ): return ngettext( "second", "seconds", nr )
def UNIT_MINUTE( nr ): return ngettext( "minute", "minutes", nr )
def UNIT_HOUR( nr ): return ngettext( "hour", "hours", nr )
def UNIT_DAY( nr ): return ngettext( "day", "days", nr )

# emails
def SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_SUBJECT(): return _( "Attempt to log in with your email" )
def SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_BODY( link, email ): return _( "An attempt was made to log in to your account using this email address. If you'd like to use your email to log in, you need to set a password for it: %(link)s (click or copy and paste in your browser)", link = link, email = email )
def SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_SUBJECT(): return _( "Attempt to register with your email" )
def SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_BODY( link, email ): return _( "An attempt was made to sign up to your account. If you've forgotten your password, you can reset it: %(link)s (click or copy and paste in your browser)", link = link, email = email )
def SEND_EMAIL_REGISTER_CONFIRM_SUBJECT(): return _( "Registration confirmation" )
def SEND_EMAIL_REGISTER_CONFIRM_BODY( link ): return _( "Follow this link to confirm your registration: %(link)s (click or copy and paste in your browser)", link = link )
def SEND_EMAIL_EMAIL_CHANGE_CONFIRM_SUBJECT(): return _( "Confirm new email" )
def SEND_EMAIL_EMAIL_CHANGE_CONFIRM_BODY( link, email ): return _( "A request to change the email address linked to your account was made. Follow this link to confirm the change to address %(email)s: %(link)s (click or copy and paste in your browser)", email = email, link = link )
def SEND_EMAIL_EMAIL_CHANGE_UNDO_SUBJECT(): return _( "Undo change email" )
def SEND_EMAIL_EMAIL_CHANGE_UNDO_BODY( link, email ): return _( "A request to change the email address linked to your account was made. Follow this link to cancel the change and ensure the current address %(email)s remains linked to your account: %(link)s (click or copy and paste in your browser)", email = email, link = link )
def SEND_EMAIL_PASSWORD_RESET_SUBJECT(): return _( "Password reset" )
def SEND_EMAIL_PASSWORD_RESET_BODY( link ): return _( "A request to reset your password was made. Follow this link to reset your password and set a new one: %(link)s (click or copy and paste in your browser)", link = link )
def SEND_EMAIL_AUTH_NEW_SUBJECT(): return _( "New authentication" )
def SEND_EMAIL_AUTH_NEW_BODY( link, provider_name, provider_uid ): return _( "A new authentication method has been added: you can now log in using %(provname)s. (If you do not remember logging in using %(provname)s, your %(provname)s account - Id %(provuid)s may have been be compromised. In addition, you should log in to your account profile and remove the %(provname)s authentication method. %(link)s (click or copy and paste in your browser)", link = link, provname = provider_name, provuid = provider_uid )
def SEND_EMAIL_ACCOUT_DELETE_SUBJECT(): return _( "Account deletion" )
def SEND_EMAIL_ACCOUT_DELETE_BODY( link ): return _( "A request to delete your account was made. Follow this link to confirm deletion - WARNING: this cannot be undone! - %(link)s (click or copy and paste in your browser)", link = link )
def SEND_EMAIL_ACCOUT_POSTS_DELETE_SUBJECT(): return _( "Account and forum posts deletion" )
def SEND_EMAIL_ACCOUT_POSTS_DELETE_BODY( link ): return _( "A request to delete your account and your forum posts was made. Follow this link to confirm deletion - WARNING: this cannot be undone! - %(link)s (click or copy and paste in your browser)", link = link )

# display name
def DISPLAY_NAME_DELETED_DISPLAY(): return _( "[Deleted user]" )
def DISPLAY_NAME_INTRO(): return _( "Your display name is your public Id. You must have a display name to post in the forums, invite friends and join games." )
def DISPLAY_NAME_AUTO_GENERATED(): return _( "(The display name above was randomly generated, feel free to change it.)" )
def DISPLAY_NAME_ALREADY_USED(): return _( "The name you have chosen is already in use. Please enter a new name." )
def DISPLAY_NAME_WRONG_SYMBOLS(): return _( "Your name contains forbidden symbols. Please ensure it contains only letters or digits." )
def DISPLAY_NAME_WRONG_LENGTH( length ): return ngettext( "Your name is %(length)s character long.", "Your name is %(length)s characters long.", length, length = length )
def DISPLAY_NAME_TOO_SHORT_LENGTHEN( length ): return ngettext( "It is too short. Please ensure it is at least %(length)s character long.", "It is too short. Please ensure it is at least %(length)s characters long.", length, length = length )
def DISPLAY_NAME_TOO_LONG_SHORTEN( length ): return ngettext( "It is too long. Please ensure it is maximum %(length)s character long.", "It is too long. Please ensure it is maximum %(length)s characters long.", length, length = length )

# forums
def POST_DELETED_DISPLAY(): return _( "[Deleted post]" )
def USER_NOT_EXIST(): return _( "The user you requested does not exist or was deleted." )
def FORUM_NOT_EXIST(): return _( "The forum you requested does not exist or was deleted." )
def POST_THREAD_NOT_EXIST(): return _( "The post or thread you requested does not exist or was deleted." )
def POST_NOT_EXIST(): return _( "The post you requested does not exist or was deleted." )
def THREAD_TITLE_NEEDED(): return _( "Your thread needs a title." )
def POST_BODY_NEEDED(): return _( "Your post needs to contain some text." )
def THREAD_TITLE_TOO_LONG( exceed ): return ngettext( "Your thread title is too long by %(exceed)s character.", "Your thread title is too long by %(exceed)s characters.", exceed, exceed = exceed )
def POST_BODY_TOO_LONG( exceed ): return ngettext( "Your post is too long by %(exceed)s character.", "Your post is too long by %(exceed)s characters.", exceed, exceed = exceed )
def FAIL_THREAD_SUBMISSION(): return _( "Thread submission failed. Please try again." )
def FAIL_POST_SUBMISSION(): return _( "Post submission failed. Please try again." )
def FAIL_POST_MODIFICATION(): return _( "Post modification failed. Please try again." )
def FAIL_POST_DELETION(): return _( "Post deletion failed. Please try again." )

# friends
def DISPLAY_NAME_NOT_EXIST(): return _( "The name you entered is invalid. Please enter the user name of the person you'd like to invite to be your friend." )

# OAuth
def CONNECT_WITH_GOOGLE(): return _( "Sign in with Google" )
def CONNECT_WITH_FACEBOOK(): return _( "Login with Facebook" )
def CONNECT_WITH_STEAM(): return _( "Sign in through Steam" )
def CONNECT_WITH_TWITTER(): return _( "Sign in with Twitter" )

