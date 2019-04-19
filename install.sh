#!/bin/bash

mkdir /home/$USER/.local/share/redeliste
cp $PWD/data/files/* /home/$USER/.local/share/redeliste/

path_desktop="/home/$USER/.local/share/applications/redeliste.desktop"

cp $PWD/data/starter/redeliste.desktop $path_desktop

echo "Exec=/home/$USER/.local/share/redeliste/redeliste.py" >> $path_desktop
echo "Icon=/home/$USER/.local/share/redeliste/redeliste.png" >> $path_desktop

/home/$USER/.local/share/redeliste/redeliste.py

