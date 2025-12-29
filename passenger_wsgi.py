import imp
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))


wsgi = imp.load_source('wsgi', 'run.py')
application = wsgi.app

os.environ['RECAPTCHA_SITE_KEY'] = '6LfpGBAsAAAAAN40acZz7e_iuU1GkfCgVyamYGgy'
os.environ['RECAPTCHA_SECRET_KEY'] = '6LfpGBAsAAAAALn5Sm58lLca6T3nIcMFUQDrVwPw'