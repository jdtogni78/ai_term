from .stderr_buffer import StderrBuffer

verbose = False

class StderrCollector:
    def __init__(self, max_entries):
        self.collected_content = ""
        self.collecting = False
        self.stderr_lines = StderrBuffer(max_entries)

    def has_key(self, key): return any(line.get(key) for line in self.stderr_lines)
    
    def stop(self):
        self.collecting = False
        self.add()

    def add(self):
        if self.collecting and self.collected_content:
            self.stderr_lines.append("err", self.collected_content)
        self.collected_content = ""

    def append(self, line):
        self.collecting = True
        if (verbose): print("collecting")
        self.collected_content += line

    def add_other(self, key, value):
        if key and value:
            self.stderr_lines.append(key, value)

    def last_error(self, n):
        # get the last err element + all following elements, 
        # plus the previous n-1 elements
        # return a list of entries
        result = []
        found = -1
        for i in range(len(self.stderr_lines)-1, -1, -1):
            # print(i, found, n, found + n, self.stderr_lines[i])
            result.append(self.stderr_lines[i])
            if found == -1 and "err" in self.stderr_lines[i]:
                found = i
            if found != -1 and i <= found + n:
                break
        return result
    
    def show(self):
        # show a numbered list of errors
        for i, line in enumerate(self.stderr_lines):
            print(f"{i}. {line}")

    def get_items(self, indexes: list[int]):
        return [self.stderr_lines[i] for i in indexes]