from collections import deque

class OutputCollector:
    def __init__(self, max_size=20):
        self.max_size = max_size
        self.output = deque(maxlen=max_size)
    
    def add(self, key, value):
        if not key or not value:
            return
        if not key.strip() or not value.strip():
            return
        self.output.append({key: value})
    
    def get_last(self, n):
        return list(self.output)[-n:]
    
    def __len__(self):
        return len(self.output)
    
    def __getitem__(self, index):
        return self.output[index]