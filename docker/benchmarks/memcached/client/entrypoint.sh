#!/bin/bash

python3.7 ./entrypoint.py $@
tail -f /dev/null
