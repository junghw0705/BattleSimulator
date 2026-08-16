import os
import sys

# Ensure BattleSimulator subfolder is on sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
sub_dir = os.path.join(root_dir, "BattleSimulator")
if sub_dir not in sys.path:
    sys.path.insert(0, sub_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import and execute the main app logic
import app as main_app
