# config.py
import os
from dotenv import load_dotenv

load_dotenv()


def get_env_int(var_name, default):
    try:
        return int(os.getenv(var_name, default))
    except ValueError:
        print(f"Warning: {var_name} is not a valid int, using default {default}")
        return default


def get_env_float(var_name, default):
    try:
        return float(os.getenv(var_name, default))
    except ValueError:
        print(f"Warning: {var_name} is not a valid float, using default {default}")
        return default


# OPTIMIZED SETTINGS FOR REAL-TIME DETECTION
# Increased thresholds to reduce false positives (bending, sitting)
FPS = get_env_int("FPS", 30)
WINDOW_SIZE = get_env_int("WINDOW_SIZE", 10)  # Increased for more stable detection

# Fall detection thresholds - balanced for real-world detection
V_THRESH = get_env_float("V_THRESH", 65.0)  # Velocity threshold - lowered for better detection
DY_THRESH = get_env_float("DY_THRESH", 25.0)  # Vertical drop threshold
ASPECT_RATIO_THRESH = get_env_float("ASPECT_RATIO_THRESH", 0.50)  # Body flatten threshold

# Alert cooldown to prevent spam (seconds)
ALERT_COOLDOWN = get_env_float("ALERT_COOLDOWN", 3.0)
