import os
from datetime import datetime
LOG_DIR = os.getenv('LOG_DIR', './logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f'backup_{datetime.now().strftime("%Y%m%d")}.log')

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
