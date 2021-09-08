#!/bin/bash

echo -e "\033[0;32mBuilding site.\033[0m"

jekyll build --trace

echo -e "\033[0;32mCopying to git repo.\033[0m"
FILES=_site/*
for f in $FILES
do
  echo "Processing $f file..."
  cp $f /Users/johnmclevey/Documents/work/career/websites/mclevey.github.io/
done

echo -e "\033[0;32mPushing changes.\033[0m"
cd /Users/johnmclevey/Documents/work/career/websites/mclevey.github.io/ && git add . && git commit -m 'routine update' && git push

