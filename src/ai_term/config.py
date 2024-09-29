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
            'reset': colorama.Fore.RESET,
            'term': colorama.Fore.WHITE
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

    def print(self, color: str, *args, **kwargs):
        if color not in self.colors:
            raise ValueError(f"Invalid color: {color}, expected one of {self.colors.keys()}")
        # add color as first argument
        print(self.colors[color], end="")
        print(*args, **kwargs)
        print(self.colors['reset'], end="", flush=True)

class _Config:
    def __init__(self):
        self.USE_INSTRUCTOR = os.getenv('USE_INSTRUCTOR', False)
        self.AUTO_SUGGESTIONS = os.getenv('AUTO_SUGGESTIONS', False)
        self.MAX_TOKENS = os.getenv('MAX_TOKENS', None)
        self.MODEL_NAME = os.getenv('MODEL_NAME', 'llama3.1')
        self.PRINT_REASONING = os.getenv('PRINT_REASONING', self.USE_INSTRUCTOR)
        self.PRINT_STREAM = os.getenv('PRINT_STREAM', not self.PRINT_REASONING)

    def print(self):
        Colors.print("term", "\nAI Term Properties (edit .env to change):")
        Colors.print("term", "*****************************")
        Colors.print("ai_output", "USE_INSTRUCTOR:   ", end="")
        Colors.print("system", f"{self.USE_INSTRUCTOR}", end="")
        Colors.print("term", " (default: False)")
        Colors.print("ai_output", "AUTO_SUGGESTIONS: ", end="")
        Colors.print("system", f"{self.AUTO_SUGGESTIONS}", end="")
        Colors.print("term", " (default: False)")
        Colors.print("ai_output", "MAX_TOKENS:       ", end="")
        Colors.print("system", f"{self.MAX_TOKENS}", end="")
        Colors.print("term", " (default: None)")
        Colors.print("ai_output", "MODEL_NAME:       ", end="")
        Colors.print("system", f"{self.MODEL_NAME}", end="")
        Colors.print("term", " (default: llama3.1)")
        Colors.print("ai_output", "PRINT_REASONING:  ", end="")
        Colors.print("system", f"{self.PRINT_REASONING}", end="")
        Colors.print("term", " (default: same as USE_INSTRUCTOR)")
        Colors.print("ai_output", "PRINT_STREAM:     ", end="")
        Colors.print("system", f"{self.PRINT_STREAM}", end="")
        Colors.print("term", " (default: not PRINT_REASONING)")
        Colors.print("reset", "\n")
Config = _Config()
Colors = _Colors()

if __name__ == "__main__":
    Config.print()