Skutter is an information provider for Be::Shell. It currently provides MPRIS, Yahoo Weather, calendar, RSS and IMAP. The display is highly configurable using simple HTML notation. Edit mpris.format and weather.format (both in ~/.config/skutter) to obtain the display you want. 

<b>Installation</b><br>
Copy the skutter directory to /usr/share and skutter.py to anywhere in $PATH.<br>On its first run, skutter will copy the config files to ~/.config/skutter and create fifo's in ~/.local/share/skutter.

Config options are in ~/.config/skutter/skutterrc and are explained in the file. 

<b>BE::Shell Settings</b><br>
To your be.shell config you need to add something like:
```
[calendar]
Type=Label
Lines=1
FiFo=~/.local/share/skutter/calendar

[weather]
Type=Label
Lines=1
FiFo=~/.local/share/skutter/weather

[mpris]
Type=Label
Lines=1
FiFo=~/.local/share/skutter/mpris
```
Finally, you can use the dbus method org.bedevil.Skutter /Control Restart to restart script. This is needed if you change your weather or mpris formatting.

