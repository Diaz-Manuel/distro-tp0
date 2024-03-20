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
volumes:
  - \${PWD}/client/config.ini:/config.ini
entrypoint: python3 /main.py
environment:
  - CLI_ID=
  - CLI_LOG_LEVEL=DEBUG
  - NOMBRE=
  - APELLIDO=
  - DOCUMENTO=
  - NACIMIENTO=
  - NUMERO=
networks:
  - testing_net
depends_on:
  - server
"


printf 'How many clients do you want to define: '
read clients
DNIS=($(shuf -n $clients -i 9000000-45000000)) # use shuf to avoid duplicates
DOBS=($(shuf -n $clients -i $(date -j -f '%Y-%m-%d' '1970-01-01' '+%s')-$(date -j -f '%Y-%m-%d' '2005-01-01' '+%s') | xargs -I{} date -j -f '%s' '{}' '+%Y-%m-%d'))
export DNI=${DNIS[0]}
export DOB=${DOBS[0]}

export CLIENTID
for CLIENTID in $(seq $clients)
  # set clientID
  do export NEW_CLIENT=$(printf "$CLIENT" | yq '.container_name += strenv(CLIENTID) | .environment[0] += strenv(CLIENTID)')
  # set bet in environment
  export FIRSTNAME=$(sort -R examples/firstnames | head -n1)
  export LASTNAME=$(sort -R examples/lastnames | head -n1)
  export BET=$RANDOM
  NEW_CLIENT=$(printf "$NEW_CLIENT" | yq '.environment[2] += strenv(FIRSTNAME) | .environment[3] += strenv(LASTNAME) | .environment[4] += strenv(DNI) | .environment[5] += strenv(DOB) | .environment[6] += strenv(BET)')
  # append client to template
  TEMPLATE=$(printf "$NEW_CLIENT" | yq 'env(TEMPLATE) * {"services": {"client" + strenv(CLIENTID): .}}')
  # set variables for next client as array are 0 indexed
  DNI=${DNIS[$CLIENTID]}
  DOB=${DOBS[$CLIENTID]}
done

printf "$TEMPLATE\n" >docker-compose-autogen.yaml
