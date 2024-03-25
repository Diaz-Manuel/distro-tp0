#!/bin/sh
export TEMPLATE="
version: '3.9'
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    volumes:
      - \${PWD}/server/config.ini:/config.ini
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - SERVER_AGENCY_COUNT=
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
volumes:
  - \${PWD}/client/config.ini:/config.ini
  - \${PWD}/.data/agency-
entrypoint: python3 /main.py
environment:
  - CLI_ID=
  - CLI_LOG_LEVEL=INFO
networks:
  - testing_net
depends_on:
  - server
"


printf 'How many clients do you want to define: '
read clients
export clients
# tell server how many agencies need to submit bets before showing lottery results
TEMPLATE=$(printf "$TEMPLATE" | yq '.services.server.environment[2] += strenv(clients)')
export CLIENTID
for CLIENTID in $(seq $clients)
  # set clientID
  do export NEW_CLIENT=$(printf "$CLIENT" | yq '.container_name += strenv(CLIENTID) | .environment[0] += strenv(CLIENTID)')
  # mount bets csv file to agency
  NEW_CLIENT=$(printf "$NEW_CLIENT" | yq '.volumes[1] += strenv(CLIENTID) + ".csv:/agency.csv"')
  # append client to template
  TEMPLATE=$(printf "$NEW_CLIENT" | yq 'env(TEMPLATE) * {"services": {"client" + strenv(CLIENTID): .}}')
done

printf "$TEMPLATE\n" >docker-compose-autogen.yaml
