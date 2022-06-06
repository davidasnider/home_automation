#!/bin/bash

nerdctl build . -t sprinklermultiplier

echo "Running the Sprinkler Multiplier"
nerdctl run --env-file .env --rm sprinklermultiplier

echo "Running Update Magic Mirror"
nerdctl run --env-file .env --rm -it --net=host --entrypoint bash sprinklermultiplier -c "python3 /app/update_magic_mirror_temp.py"
