#!/usr/bin/env python3

import os
import fcntl
import sys
import argparse

import sys; 

def tee(files, append, max_lines):
    mode = 'a' if append else 'w'
    file_handles = [open(file, mode) for file in files]
    
    try:
        # Set stdin to non-blocking mode
        fd = sys.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        while True:
            try:
                byte = sys.stdin.read(1024)
                if byte:
                    sys.stdout.write(byte)
                    sys.stdout.flush()
                    for fh in file_handles:
                        fh.write(byte)
                        if byte == '\n':
                            fh.flush()
                            os.fsync(fh.fileno())
                            fh.close()
                            
                    if byte == '\n' and max_lines is not None:
                        for file in files:
                            with open(file, 'r') as f:
                                content = f.readlines()
                    
                            with open(file, 'w') as f:
                                f.writelines(content[-max_lines:])
                            
                        # Reopen file handles
                        file_handles = [open(file, 'a') for file in files]
                    
            except IOError:
                # No data available, sleep briefly to avoid busy-waiting
                import time
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        for fh in file_handles:
            fh.close()

def main():
    parser = argparse.ArgumentParser(description='Mimic the shell tee command')
    parser.add_argument('files', nargs='*', help='File(s) to write to')
    parser.add_argument('-a', '--append', action='store_true', help='Append to the given files, do not overwrite')
    parser.add_argument('-n', '--lines', type=int, default=None, help='Number of lines to keep')
    args = parser.parse_args()

    tee(args.files, args.append, args.lines)

if __name__ == '__main__':
    main()
