# ilarisdiscordbot
A work in progress discord bot for the [ilaris](https://ilarisblog.wordpress.com/downloads/) ttrpg.

If you use this dev version, make sure that the bot can only be invited by you.
Otherwise, others can view your log and groups without administrator rights. 

## How to use
Needs to be updated

### GeneralCommands
  - `helloilaris` Prints a hello user message   
  - `ilaris`        Posts an image of the given page if argument is numeric. Else...
  - `r`             Rolls a die. Special named throws: {"I": "1d20", "III": "3d20", "I+": "1@2d20", "I++": "1@3d20", "III+": "2@4d20", "III++": "2@5d20",
                       "+": "2@4d20", "++": "2@5d20"}
### GroupCommands
  - `gcreate`       Creates a new group with yourself as the GM
  - `gdestroy`      Destroys a group that you've created
  - `gjoin`         Join a group as a player
  - `gleave`        Leave a group as a player
  - `glist`         List all groups
  - `gset`          Sets a group key like 'uhrzeit'. Setting 'spieler' below the...
  - `remove_player` Removes a player from your group 
### No Category:
  - `help`          Shows this message

Type `!help command` for more info on a command (including parameter descriptions).
You can also type `!help category` for more info on a category.

## How to host
This guide is not final. It is not very well written, but only for those who really want
to hose this bot right now. This guide will only cover linux, but as we are talking about
python there won't be great changes... probably.

If you want to host this bot, please be aware that it is work in progress.
Bugs will still occur and you alone are responsible for including it in your servers.

### Get a bot token
First you need to acquire a bot token.

### Clone the repository and install missing dependencies
Clone the repository
```sh
git@github.com:XaverStiensmeier/ilarisdiscordbot.git
```
Create a virtual environment
```sh
python3 -m venv ~/.venvs/discordbot
```
Install dependencies (mainly `pyyaml` and `discord.py`)
```
pip install -r /path/to/requirements.txt
```

### Add missing files/folders
I might be forgetting some. If you encounter issues regarding missing files,
open an issue and I will write more about what's needed.
#### Large Folders
1. `resources/manoeverkarten/` is a folder containing `Manöverkarten` [Gatsu's Manöverkartenplugin](https://dsaforum.de/viewtopic.php?p=2002977#p2002979)
2. `resources/ilaris/` is a folder containing the core rules as image files (`ilaris-001.png`, ..., `ilaris-219.png`)

##### Converting PDFs to images
In order to convert pdfs to images use from
```sh
sudo apt install poppler-utils
```
the command
```sh
pdftoppm -png FileIn.pdf outName
```
[Need more info on converting PDFs to images?](https://www.tecmint.com/convert-pdf-to-image-in-linux-commandline/)
#### Private Data Folders
1. `resources/token` is a file containing your token.
2. `resources/groups/groups.yml` is a file containing existing groups

### Actually hosting
Run
```sh
./ilaris_bot.py
```
As long as `ilaris_bot` is running, your ilarisdiscordbot instance is up. Enjoy.

Check the `discord.log` file if anything goes wrong.
