import datetime


# log_file = config['main_log_file']
# /app/logs/{DATE}_main.log
accesslog = './access.log'
errorlog = './error.log'
loglevel = 'info'  # Adjust the log level as needed (debug, info, warning, error, critical)

# Configure logging format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'