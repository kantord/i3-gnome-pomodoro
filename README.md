# i3-gnome-pomodoro
Integrate gnome-pomodoro into i3

## About
i3-gnome-pomodoro uses dbus to integrate gnome-pomodoro into i3. Currently it supports the following features:
- View timer status in a terminal, and therefore
- Show timer status on i3bar

## Usage
### Terminal
Timer status can be viewed by simply running `python pomodoro-clienty.py`. Example output:

    $ python pomodoro-client.py
    Pomodoro 15:35

### i3bar
Unfortunately, i3status cannot be used to display a custom feature on i3bar. However, another application can use i3status to collect information and combine it with custom features. A very simple way to do that is to create a script in this fashion:
```
#!/usr/bin/env bash

i3status -c ~/.i3/i3status.conf | while :
do
  read line
  pomodoro=`python ~/repos/i3-gnome-pomodoro/pomodoro-client.py`
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
