"""
Script to add timed backgrounds in Zorin OS 16.
github: https://github.com/Arthurdw/Zorin-Background

MIT License

Copyright (c) 2021 Arthur

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from distutils.dir_util import copy_tree
from glob import glob
from logging import basicConfig, DEBUG, debug
from os import path, geteuid
from re import findall, search
from subprocess import call
from sys import argv
from typing import List, Dict
from xml.etree import ElementTree

import click_completion
from click import group, option, argument
from colorama import init as colorama_init, Fore, Style

colorama_init()
click_completion.init()

ZORIN_WALLPAPERS_DIR = "/usr/share/backgrounds"
ZORIN_DEFAULT_WALLPAPERS = "/usr/share/gnome-background-properties/zorin-default-wallpapers.xml"
ZORIN_OTHER_WALLPAPERS = "/usr/share/gnome-background-properties/zorin-os-16-wallpapers.xml"


def extract_wallpapers(wallpaper_path: str) -> List[Dict[str, str]]:
    debug("Extracting xml contents from %s..." % wallpaper_path)
    contents = ElementTree.parse(wallpaper_path)
    debug("Successfully extracted wallpapers from %s, started parsing them..." % wallpaper_path)
    parsed = list(map(
        lambda wallpaper: dict(map(
            lambda wp: (wp.tag, wp.text),
            wallpaper
        )),
        contents.getroot()
    ))
    debug("Successfully parsed %i wallpapers from %s!" % (len(parsed), wallpaper_path))
    return parsed


@group()
@option("-v", "--verbose", is_flag=True, help="Enable debug logging/verbose content")
def cli(verbose):
    if verbose:
        basicConfig(level=DEBUG)


@cli.command(help="Get all current registered wallpapers!")
def backgrounds():
    default_wallpapers = extract_wallpapers(ZORIN_DEFAULT_WALLPAPERS)
    other_wallpapers = extract_wallpapers(ZORIN_OTHER_WALLPAPERS)

    def out(intent: int, text: str, color: str = ""):
        print(" " * intent + color + text + Style.RESET_ALL)

    def print_wallpapers(wallpapers: List[Dict[str, str]]):
        for wallpaper in wallpapers:
            out(2, f"{wallpaper['name']}:", Fore.CYAN)
            file_path = wallpaper['filename']

            if file_path.endswith(".xml"):
                file_path = Fore.LIGHTBLUE_EX + Style.BRIGHT + file_path

            out(4, f"filename: {file_path}", Style.DIM)
            out(4, f"options: {wallpaper['options']}, "
                   f"shade type: {wallpaper['shade_type']}, "
                   f"pcolor: {wallpaper['pcolor']}, "
                   f"scolor: {wallpaper['scolor']}", Style.DIM)
            print()

    out(0, "Default wallpapers:", Fore.LIGHTCYAN_EX)
    print_wallpapers(default_wallpapers)
    print()
    out(0, "Other wallpapers:", Fore.LIGHTCYAN_EX)
    print_wallpapers(other_wallpapers)


@cli.command(help="Register a new dynamic background!")
@option("-n", "--name", default=None, help="The background its name, default will be the directory name.")
@option("-h", "--hours", default=24, type=int,
        help="The amount of hours it should take for this background to cycle, default is 24.")
@option("-m", "--minutes", default=0, type=int, help="Add minutes to the hours option.")
@option("-s", "--seconds", default=0, type=int, help="Add seconds to the hours option.")
@argument("directory")
def register(name, hours, minutes, seconds, directory):
    debug("Checking if directory %s exists!", directory)
    if not path.exists(directory):
        print(Style.BRIGHT + Fore.RED + f"Directory `{directory}` could not be found!" + Style.RESET_ALL)
        return
    elif not path.isdir(directory):
        print(Style.BRIGHT + Fore.RED + f"File `{directory}` is not a directory, "
                                        "which is required for zbg to configure the timed background!" + Style.RESET_ALL)
        return
    elif geteuid() != 0:
        print(Fore.YELLOW + "In order to manipulate some files sudo access is required." + Style.RESET_ALL)
        call(['sudo', 'python3', *argv])
        exit()

    _directory = directory

    if directory[-1] == "/":
        _directory = directory[:-1]

    images = sorted(
        [img for img in glob(f"{_directory}/*.*") if search(r"\d.(jpg|png)", img)],
        key=lambda x: int(findall(r"(\d+)", x)[0])
    )

    if not images:
        print(Style.BRIGHT + Fore.RED + "No JPG or PNG files were found in", directory + Style.RESET_ALL)
        return

    dirname = path.dirname(directory)
    name = str(name or path.basename(dirname)).lower()

    print(f"Started copying {len(images)} images from `{dirname}`...")
    copy_tree(directory, f"{ZORIN_WALLPAPERS_DIR}/{name}/")
    print("Successfully copied files, starting config generation...")

    debug("Started preparing starttime.")
    start_time = {
        "year": 2021,
        "month": 0,
        "day": 0,
        "hour": 0,
        "minute": 0,
        "second": 0
    }

    data = "<background>\r\n"

    data += "\t<starttime>\r\n"
    for k, v in start_time.items():
        data += f"\t\t<{k}>{v}</{k}>\r\n"

    data += "\t</starttime>\r\n\r\n"

    duration = round((hours * 3600 + minutes * 60 + seconds) / len(images), 1)
    debug("Image duration will be %.1f seconds!" % duration)

    last = path.basename(images[-1])

    img_data: List[str] = []

    for img in images:
        img = path.basename(img)
        debug("Preparing config for %s.." % img)
        dt = ""
        dt += "\t<transition type=\"overlay\">\r\n"
        dt += f"\t\t<duration>{duration}</duration>\r\n"
        dt += f"\t\t<from>{ZORIN_WALLPAPERS_DIR}/{name}/{last}</from>\r\n"
        dt += f"\t\t<to>{ZORIN_WALLPAPERS_DIR}/{name}/{img}</to>\r\n"
        dt += "\t</transition>\r\n"
        img_data.append(dt)
        last = img
        debug("Prepared config for %s" % img)

    data += "\r\n".join(img_data)
    data += "</background>\r\n"

    print("Successfully generated config, starting to write the config...")
    config_location = f"{ZORIN_WALLPAPERS_DIR}/{name}/{name}-timed.xml"

    with open(config_location, "w+") as f:
        f.write(data)

    print("Successfully wrote the config, starting generation of gnome registration...")
    wallpapers = extract_wallpapers(ZORIN_OTHER_WALLPAPERS)
    final_name = name.capitalize()
    wallpapers = [wp for wp in wallpapers if wp["name"] != final_name]
    wallpapers.append({
        "name": final_name,
        "filename": path.abspath(config_location),
        "options": "zoom",
        "pcolor": "#000000",
        "scolor": "#000000",
        "shade_type": "solid"
    })

    registration_data = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n" \
                        "<!DOCTYPE wallpapers SYSTEM \"gnome-wp-list.dtd\">\r\n" \
                        "<wallpapers>\r\n"

    for wallpaper in wallpapers:
        registration_data += " " * 2 + "<wallpaper>\r\n"
        for k, v in wallpaper.items():
            registration_data += " " * 4 + f"<{k}>{v}</{k}>\r\n"
        registration_data += " " * 2 + "</wallpaper>\r\n"

    registration_data += "</wallpapers>\r\n"

    print("Successfully generated the gnome registration, starting to write gnome registration...")

    with open(ZORIN_OTHER_WALLPAPERS, "w+") as f:
        f.write(registration_data)

    print("Successfully wrote the gnome registration.")
    print(Fore.LIGHTGREEN_EX + f"Your timed background `{final_name}` has been added with a lifecycle of {duration}s!",
          Style.RESET_ALL)


if __name__ == "__main__":
    cli()
