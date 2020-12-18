#!/bin/bash

docker pull mongo
docker run -d --network host --name mongo-db -e MONGO_INITDB_ROOT_USERNAME=mongoadmin -e MONGO_INITDB_ROOT_PASSWORD=secret mongo:latest

