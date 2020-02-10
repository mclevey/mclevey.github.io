#!/bin/bash

echo -e "\033[0;32mBuilding site.\033[0m"

jekyll build

echo -e "\033[0;32mCopying to git repo.\033[0m"
cp -r _site /Users/johnmclevey/Documents/websites/mclevey.github.io


echo -e "\033[0;32mPushing changes.\033[0m"
cd /Users/johnmclevey/Documents/websites/mclevey.github.io
git add . && git commit -m 'routine update' && git push
