#!/bin/bash

nerdctl build . -t sprinklermultiplier
nerdctl run --env-file .env --rm sprinklermultiplier
