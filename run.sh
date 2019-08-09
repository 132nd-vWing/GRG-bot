#!/bin/bash

docker stop grg-bot
docker rm grg-bot
docker run -it --env-file=environment --name=grg-bot grg-bot:latest 
