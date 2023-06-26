#!/bin/bash

ZIP=`command -v zip`
if [ -z "$ZIP" ]; then
  echo "Error: zip command not available"
  exit
fi

$ZIP -r APSPark collect_bc.py init_matrix.py in_memory.py my_util.py

if [ ! -f "APSPark.zip" ]; then
  echo "Error: no ssabna.zip, something went wrong!"
else
  echo "Done!"
fi
