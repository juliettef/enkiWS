import os

# # Initialise
# # extract all
# os.system( 'pybabel extract -o ./locale/messages.pot ./' )
# # extract using babel.cfg
# os.system( 'pybabel extract -F ./babel.cfg -o ./locale/messages.pot ./' )
# # initialise
# os.system( 'pybabel init -l fr_FR -d ./locale -i ./locale/messages.pot' )
# os.system( 'pybabel init -l en_US -d ./locale -i ./locale/messages.pot' )
# os.system( 'pybabel init -l es_ES -d ./locale -i ./locale/messages.pot' )

# Update template
os.system( 'pybabel extract -F ./babel.cfg -o ./locale/messages.pot ./ --no-wrap --sort-by-file' )

# Update language
os.system( 'pybabel update -l fr_FR -d ./locale/ -i ./locale/messages.pot --no-wrap' )
# os.system( 'pybabel update -l en_US -d ./locale/ -i ./locale/messages.pot --no-wrap' )
# os.system( 'pybabel update -l es_ES -d ./locale/ -i ./locale/messages.pot --no-wrap' )

# Compile
os.system( 'pybabel compile -f -d ./locale --statistics' )
