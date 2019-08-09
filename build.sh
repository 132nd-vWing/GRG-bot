#!/bin/bash

set -e

rm -rf build
mkdir -p build
cd build
ln ../{Dockerfile,main.py,config.py,help.py,grg-test.tex,grg.sty,arg.py,texlive.profile,doc/QESHM_airfield.png} .
sudo docker build -t grg-bot .
