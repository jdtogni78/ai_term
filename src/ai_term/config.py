from typing import Dict
import colorama
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Colors configuration
class _Colors:
    def __init__(self):
        self.colors = {
            'ai_output': colorama.Fore.CYAN,
            'user_input': colorama.Fore.GREEN,
            'system': colorama.Fore.YELLOW,
            'error': colorama.Fore.RED,
            'warning': colorama.Fore.YELLOW,
            'reset': colorama.Fore.RESET
        }
        self.read_colors_from_env()

    def read_colors_from_env(self):
        for color_name, default_color in self.colors.items():
            env_var = f"{color_name.upper()}_COLOR"
            color_value = os.getenv(env_var, default_color)
            setattr(self, color_name, color_value)

    def ai_output(self) -> str:
        return self.colors['ai_output']

    def user_input(self) -> str:
        return self.colors['user_input']

    def system(self) -> str:
        return self.colors['system']

    def error(self) -> str:
        return self.colors['error']

    def warning(self) -> str:
        return self.colors['warning']

    def reset(self) -> str:
        return self.colors['reset']
    
    def set_color(self, color: str):
        print(self.colors[color], end="", flush=True)

    def print(self, color: str, *args):
        if color not in self.colors:
            raise ValueError(f"Invalid color: {color}, expected one of {self.colors.keys()}")
        print(self.colors[color], *args, self.colors['reset'], flush=True)
        # print(self.colors['reset'])

class _Config:
    def __init__(self):
        self.USE_INSTRUCTOR = os.getenv('USE_INSTRUCTOR', False)

Config = _Config()
Colors = _Colors()
