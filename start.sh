#!/bin/bash

# requires python 3.9

pip install -r requirements.txt

mkdir -p ./logs

touch ./logs/output.std.log
touch ./logs/output.err.log
touch ./logs/access.log

echo "Starting gunicorn"

gunicorn \
    --bind 0.0.0.0:2000 \
    --threads 8 \
    --error-logfile ./logs/output.err.log \
    --log-file ./logs/output.std.log \
    --capture-output \
    --certfile=${CERT_PATH}/cert.pem \
    --keyfile=${CERT_PATH}/privkey.pem \
    --access-logfile ./logs/access.log \
    application:application &

echo "Tailing"

tail -f ./logs/output.std.log  -f ./logs/output.err.log  -f ./logs/access.log 