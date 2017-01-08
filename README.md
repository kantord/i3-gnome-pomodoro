# i3-gnome-pomodoro
Integrate gnome-pomodoro into i3

## About
i3-gnome-pomodoro uses dbus to integrate gnome-pomodoro into i3. Currently it supports the following features:
- View timer status in a terminal, and therefore
- Show timer status on i3bar
- Control pomodoro state in a terminal, and therefore
- Control pomodoro state using bindsym (keyboard and mouse shortcuts)

Here's what i3-gnome-pomodoro looks like on my i3bar:
![Pomodoro 24:45 |  075%    uvsFvTK7SffCNaP9 |  |    100% |    100% |    55°C |  24.6 GB |    01. 07    23.19 |  70%](screenshot.png?raw=true)

## Usage and setup
### Dependencies
i3-gnome-pomodoro needs the following Python packages to be installed:
* click
* pydbus

You can install them using `pip install -r requirements.txt`. Might require `sudo` when installing system-wide. Obviously, you'll also need to have [gnome-pomodoro](http://gnomepomodoro.org/) installed already.
That's it. i3-gnome-pomodoro then should work from the terminal out-of-the-box. But to make it more integrated into i3 and more convenient to use, you might want to set it up with i3bar and put key bindings into your i3 config. So please read along!

### Terminal
Timer status can be viewed by simply running `python pomodoro-client.py`. Example output:

    $ python pomodoro-client.py status
    Pomodoro 15:35

The timer state can be manipulated using the commands `pause`, `resume`, `start`,
`stop`, `skip`, `toggle` and `reset`. For example:

    $ python pomodoro-client.py pause


### i3bar
Unfortunately, i3status cannot be used to display a custom feature on i3bar. However, another application can use i3status to collect information and combine it with custom features. A very simple way to do that is to create a script in this fashion:
```
#!/usr/bin/env bash

i3status -c ~/.i3/i3status.conf | while :
do
  read line
  pomodoro=`python ~/repos/i3-gnome-pomodoro/pomodoro-client.py status`
  echo "$pomodoro| $line" || exit 1
done
```

After saving that script, make sure you update your i3 config to set it as your `status_command`:
```
bar {
        status_command ~/repos/arch-config/i3status.sh
}
```

And then restart i3 so the changes be in effect right away:

    $ i3-msg restart

If you want to use an i3status replacement, please follow its respective documentation to get information about how you can use i3-gnome-pomodoro.

### Refresh rate
i3-gnome-pomodoro displays a countdown timer on i3bar. If you use i3status, setting `resfresh_rate` in your i3status configuration can probably result in a better user experience. I personally use this configuration:

```
general {
    interval = 1
}
```

### Keyboard shortcuts
I use the following key bindings in my i3 config:
```
bindsym $mod+F9 exec "python ~/repos/i3-gnome-pomodoro/pomodoro-client.py start"
bindsym $mod+F10 exec "python ~/repos/i3-gnome-pomodoro/pomodoro-client.py toggle"
bindsym $mod+F11 exec "python ~/repos/i3-gnome-pomodoro/pomodoro-client.py skip"
bindsym $mod+F12 exec "python ~/repos/i3-gnome-pomodoro/pomodoro-client.py stop"
```
