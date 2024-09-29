import json
from ai_term.symbols import SYMBOL_CMD

class StderrBuffer:
    # will contain [{key : value}, {key : value}, {key : value}]
    def __init__(self, max_size=20):
        self.max_size = max_size
        self.array = []
        self.group_start = SYMBOL_CMD
    
    def append(self, key, value):
        # ignore when value or key is empty or empty string
        if not key or not value: return
        if not key.strip() or not value.strip(): return
        self.array.append({key : value})
        # keep the buffer at max_size
        while len(self.array) > self.max_size:
            self.array.pop(0)
        self.persist()

    def persist(self):
        # print one line at a time
        with open("/tmp/stderr_buffer.json", "w") as f:
            for line in self.array:
                json.dump(line, f)
                f.write("\n")

    def load(self):
        with open("/tmp/stderr_buffer.json", "r") as f:
            self.array = [json.loads(line) for line in f]
        
    def get_groups(self):
        groups = []
        group = []
        # groups are sequences of lines, starting with an group_start key
        for line in self.array:
            first_key = next(iter(line))
            if self.group_start in first_key:
                groups.append(group)
                group = []
            group.append(line)
        if group:
            groups.append(group)
        return groups
    
    def pop(self):
        value = self.array.pop()
        self.persist()
        return value
    
    def __str__(self): return str(self.array)
    def __iter__(self): return iter(self.array)
    def __len__(self): return len(self.array)
    def __getitem__(self, index): return self.array[index]