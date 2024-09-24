SYMBOL_CHOICE = "🔘"
SYMBOL_QUESTION = "❓"
SYMBOL_CMD = "⚡"
SYMBOL_PROMPT = "👤"

def replace_symbols(prompt):
    prompt = prompt.replace(SYMBOL_CHOICE, "choice: ")
    prompt = prompt.replace(SYMBOL_QUESTION, "question: ")
    prompt = prompt.replace(SYMBOL_CMD, "cmd: ")
    prompt = prompt.replace(SYMBOL_PROMPT, "prompt: ")
    return prompt
