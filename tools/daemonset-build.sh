#!/usr/bin/env bash
# Usage: ./daemonset-build
# Example: ./daemonset-build

set -e

docker build -t security-agent -f src/daemonset/Dockerfile .

docker tag security-agent:latest dev.local/security-agent:v1
docker save dev.local/security-agent:v1 -o security-agent.tar

scp security-agent.tar ubuntu@10.255.41.115:~
scp security-agent.tar ubuntu@10.255.41.40:~

rm security-agent.tar
docker rmi dev.local/security-agent:v1

ssh ubuntu@10.255.41.115 "sudo ctr -n k8s.io images import security-agent.tar"
ssh ubuntu@10.255.41.40 "sudo ctr -n k8s.io images import security-agent.tar"
