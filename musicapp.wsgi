import sys
import site

site.addsitedir('/var/www/serverapp/myappenv/lib/python3.8/site-packages')

sys.path.insert(0, '/var/www/serverapp')

from app import app as application
