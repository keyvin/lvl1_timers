#!/bin/bash

cd /home/keyvin/

until python3 "report server.py"; do
    echo "Script Failed, Restarting"
done
