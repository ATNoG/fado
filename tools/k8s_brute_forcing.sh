#!/usr/bin/env bash

set -e

# make sure to kill the background jobs if this script is terminated early
trap 'kill $(jobs -p) 2>/dev/null || true' EXIT

# hey -n 10000 -c 100 http://hello-serverless.default.10.255.41.115.sslip.io/  > /dev/null 2>&1 &
# hey -n 10000 -c 100 http://sentiment-analyzer.default.10.255.41.115.sslip.io > /dev/null 2>&1 &
hey -n 10000 -c 100 http://yaml-load.default.10.255.41.115.sslip.io/         > /dev/null 2>&1 &
hey -n 10000 -c 100 http://yaml-load.default.10.255.41.115.sslip.io/         > /dev/null 2>&1 &

# wait for the commands to finish
wait
