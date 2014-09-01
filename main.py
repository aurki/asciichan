import os
from webapp2 import WSGIApplication, Route

# Set useful fields
root_dir = os.path.dirname(__file__)
template_dir = os.path.join(root_dir, 'templates')

# Create the WSGI application and define route handlers
app = WSGIApplication([
    ('/', 'handlers.asciichan.AsciiPage')
], debug=True)

