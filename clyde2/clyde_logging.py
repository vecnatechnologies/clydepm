import logging

def init_logging(level = logging.ERROR):
  # create logger with 'spam_application'
  logger = logging.getLogger('clyde2')
  logger.setLevel(logging.DEBUG)
  # create file handler which logs even debug messages
  fh = logging.FileHandler('clyde2.log')
  fh.setLevel(logging.DEBUG)
  # create console handler with a higher log level
  ch = logging.StreamHandler()
  ch.setLevel(level)
  # create formatter and add it to the handlers
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  plain_formatter = logging.Formatter('%(message)s')
  fh.setFormatter(formatter)
  ch.setFormatter(plain_formatter)
  # add the handlers to the logger
  logger.addHandler(fh)
  logger.addHandler(ch)

def get_logger():
  return logging.getLogger('clyde2') 
