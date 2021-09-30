# Zorin Background

A python script which has the same idea as
[adi1090x his dynamic wallpaper](https://github.com/adi1090x/dynamic-wallpaper) but implemented for Zorin OS.

The script makes use of the build in timed backgrounds from Zorin OS.

## Installation

```bash
git clone https://github.com/Arthurdw/Zorin-Background.git
cd Zorin-Background
sudo python3 -m pip install -r requirements.txt
python3 zbg.py
```

## Usage

`python3 zbg.py register ./forest/`

### Note:

The images form the directory must be a JPG or PNG, all images which are not named as a number will be ignored. Images
are cycled in order. (by their filename)

## Applying the background

After that the command has ran, you can find it in `Settings > Background`. Your OS might need to restart for the
background to work properly.

### My background isn't there!

If you can't find your background in the settings menu, please check that it is in `python3 zbg.py backgrounds`. If its
not in the prompt from that command please rerun the register command and make sure no errors occurred.
