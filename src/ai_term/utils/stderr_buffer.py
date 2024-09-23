class StderrBuffer:
    # will contain [{key : value}, {key : value}, {key : value}]
    def __init__(self, max_size=20):
        self.max_size = max_size
        self.array = []
    
    def append(self, key, value):
        # ignore when value or key is empty or empty string
        if not key or not value: return
        if not key.strip() or not value.strip(): return
        self.array.append({key : value})
        # check how many entries for that key, tracking oldest
        # remove oldest if max_size is reached
        found = None
        first = True
        count = 0
        for entry in self.array:
            if entry.get(key) == value:
                count += 1
                if first:
                    first = False
                    found = entry
        if found and count >= self.max_size:
            self.array.remove(found)
        
    def pop(self): return self.array.pop()
    def __str__(self): return str(self.array)
    def __iter__(self): return iter(self.array)
    def __len__(self): return len(self.array)
    def __getitem__(self, index): return self.array[index]