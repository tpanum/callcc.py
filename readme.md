# Call with continuation (callcc)
This repository contains an implementation of a tool that [Nicholas Carlini presented during his coding session](https://nicholas.carlini.com/writing/2020/screen-recording-breaking-adversarial-example-defense.html).

Essentially this is a tool that serves a Python interpreter through a gRPC interface.
This is particularly useful if you have scripts that contain certain expensive operations that seek to keep in memory (think Jupyter Notebooks).

## Running
	1. Copy `callcc.py` to your development directory and ensure that the `grpcio` package is available
	2. Start the sever `python -c "from callcc import run; run()"`
	3. Wrap your Python script


## Wrapping a script
Assume you have the following script (test.py):

``` python
import time

def main():
  # expensive
  total = 0
  for i in range(10):
    total += i
	time.sleep(1)

  # under development
  print(total % 12)

if __name__ == "__main__":
  main()

```

It can be wrapped by:


``` python
import time
from callcc import wrap

@wrap
def setup():
  global total = 0
  for i in range(10):
    total += i
	time.sleep(1)

@wrap
def do_next():
  global total
  print(total % 12)

if __name__ == "__main__":
  setup() # after first run of the script, this call can be removed to speed up
  do_next()

```

Now you can keep running `python test.py` iteratively, while maintain global states (remember to use the `global` keyword to share variables across function calls).
