#!/bin/sh
export TEMPLATE="
version: '3.9'
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"

export CLIENT="
container_name: client
image: client:latest
entrypoint: /client
environment:
  - CLI_ID=
  - CLI_LOG_LEVEL=DEBUG
networks:
  - testing_net
depends_on:
  - server
"

printf 'How many clients do you want to define: '
read clients
export CLIENTID
for CLIENTID in $(seq $clients)
  do TEMPLATE=$(printf "$CLIENT" | yq '.container_name += strenv(CLIENTID) | .environment[0] += strenv(CLIENTID) | env(TEMPLATE) * {"services": {"client" + strenv(CLIENTID): .}}')
done

printf "$TEMPLATE\n" >docker-compose-autogen.yaml
