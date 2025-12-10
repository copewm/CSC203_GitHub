# The address and port to bind to (0.0.0.0 is essential for containers)
bind = '0.0.0.0:5000'

# The number of worker processes (Example for 4 CPU cores: (2 * 4) + 1 = 9)
workers = 7

# The module:variable name of your Flask application instance (e.g., 'app' from app.py)
wsgi_app = 'app:app'

# Output access and error logs to stdout/stderr for Docker logging
accesslog = '-'
errorlog = '-'