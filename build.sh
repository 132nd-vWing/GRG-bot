#!/bin/bash

set -e

rm -rf build
mkdir -p build
cd build
ln ../{Dockerfile,main.py,config.py,grg-test.tex,grg.sty,texlive.profile,map.png} .
sudo docker build -t grg-bot .
