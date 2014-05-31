#!/bin/sh

./weatherbot.py 2>>log.weatherbot & tail -f log.weatherbot
