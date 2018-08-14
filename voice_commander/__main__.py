import sys
from voice_commander.gui import App
import logging

logging.basicConfig(level=logging.DEBUG)
sys.exit(App().main())