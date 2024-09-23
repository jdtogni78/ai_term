import subprocess
import os
process = subprocess.Popen(['/bin/bash'], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=os.environ)

process.stdin.write(b'echo it works!\n')
process.stdin.flush()
print(process.stdout.readline()) # 'it works!\n'

process.stdin.write(b'date\n')
process.stdin.flush()
print(process.stdout.readline()) # b'Fri Aug 30 18:34:33 UTC 2024\n'

process.stdin.write(b'echo $PS1 - $SHELL\n')
process.stdin.flush()
print(process.stdout.readline()) # b'$ '