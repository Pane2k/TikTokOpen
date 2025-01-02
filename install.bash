#!/bin/bash

sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

sudo apt install python3.10 python3.10-venv python3.10-dev
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

python3.10 -m venv venv

python3.10 -m pip install -r requirements.txt

playwright install chromium

