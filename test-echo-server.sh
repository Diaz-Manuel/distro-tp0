#!/bin/bash

# build images
docker build -f ./server/Dockerfile -t "server:latest" .
docker build -f ./client/Dockerfile -t "client:latest" .
docker pull busybox:latest

# run server + clients if any
docker compose -f docker-compose-dev.yaml up -d --build

# run tests
TEMP_FILE=random_value.log
docker run --name tester --network tp0_testing_net -it busybox:latest /bin/sh \
 -c "printf \$RANDOM | tee $TEMP_FILE | nc server 12345 >nc-output.log; cmp $TEMP_FILE nc-output.log && echo TESTS PASSED! || echo TESTS FAILED"

# clean up
docker compose -f docker-compose-dev.yaml stop -t 5
docker compose -f docker-compose-dev.yaml down
docker rm tester >/dev/null
