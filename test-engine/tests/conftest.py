import os
import sys
from pathlib import Path

# Add the test-engine directory to the Python path
engine_dir = Path(__file__).parent.parent
sys.path.insert(0, str(engine_dir))
