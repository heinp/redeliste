#!/bin/bash

# this is where the program is to be installed
installLoc=/home/$USER/.local/share/redeliste

# create installation folder, if not already existing
if [[ ! -d $installLoc ]]; then
	mkdir /home/$USER/.local/share/redeliste
fi

# install the files into the folder
cp $PWD/data/files/* /home/$USER/.local/share/redeliste/

# create desktop starter
path_desktop="/home/$USER/.local/share/applications/redeliste.desktop"

cp $PWD/data/starter/redeliste.desktop $path_desktop

echo "Exec=/home/$USER/.local/share/redeliste/redeliste.py" >> $path_desktop
echo "Icon=/home/$USER/.local/share/redeliste/redeliste.png" >> $path_desktop

# start up program
/home/$USER/.local/share/redeliste/redeliste.py

