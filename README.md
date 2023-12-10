# i3-gnome-pomodoro
Integrate gnome-pomodoro into i3. Support i3bar, polybar and waybar.

Here's what i3-gnome-pomodoro looks like on my i3bar:
![Pomodoro 24:45 |  075%    uvsFvTK7SffCNaP9 |  |    100% |    100% |    55°C |  24.6 GB |    01. 07    23.19 |  70%](screenshot.png?raw=true)

i3-gnome-pomodoro can integrate with [status-one-liner](https://github.com/kantord/status-one-liner).

You can optionally disable certain workspaces during a pomodoro. They are still accessible when you pause a pomodoro.
![Workspace 10: mail is disabled during a pomodoro.](screenshot_nagbar.png)

## About
i3-gnome-pomodoro uses dbus to integrate gnome-pomodoro into i3. Currently it supports the following features:
- View timer status in a terminal, and therefore
- Show timer status on i3bar
- Control pomodoro state in a terminal, and therefore
- Control pomodoro state using bindsym (keyboard and mouse shortcuts)
- *Optionally* suppressing dunst desktop notifications while a pomodoro is active and showing them when the break starts
- *Optionally* disabling specific workspaces (such as instant messaging) while you are on a pomodoro. You can still access those workspaces, if you pause the pomodoro.
- *Optionally* displaying a nagbar warning if you try to access a workspace that you have disabled during your pomodoro.

## Usage and setup

### Install

To install 3i-gnome-pomodoro, you can use pipx:

```bash
pipx install i3-gnome-pomodoro
```

This is the recommended way.

#### AUR
**Note:** The recommended way to install i3-gnome-pomodoro is through pipx. The AUR package is not maintained
by me.

`i3-gnome-pomodoro` is available on [AUR](https://aur.archlinux.org/packages/i3-gnome-pomodoro-git), you can install it with your favorite package manager:
``` sh
$ yay -S i3-gnome-pomodoro-git
```

#### Local development

Use `poetry` to install local development dependencies:

```bash
poetry install
```

This is not required for normal usage, only if you want to make changes to i3-gnome-pomodoro.

### Terminal
Timer status can be viewed by simply running `./pomodoro-client.py`. Example output:

    $ ./pomodoro-client.py status
    Pomodoro 15:35

The timer state can be manipulated using the commands `pause`, `resume`, `start`,
`stop`, `skip`, `toggle` and `reset`. For example:

    $ ./pomodoro-client.py pause


### i3bar
Unfortunately, i3status cannot be used to display a custom feature on i3bar. However, another application can use i3status to collect information and combine it with custom features. A very simple way to do that is to create a script in this fashion:
```
#!/usr/bin/env bash

i3status -c ~/.i3/i3status.conf | while :
do
  read line
  pomodoro=`~/repos/i3-gnome-pomodoro/pomodoro-client.py status`
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

### polybar

I use the following module in polybar:

```
[module/pomodoro]
type = custom/script
exec = i3-gnome-pomodoro status
interval = 1
```

with the `i3-gnome-pomodoro status --always` flag thing like the block below, becomes possible

```
[module/pomodoro]
type = custom/script
click-left = i3-gnome-pomodoro toggle
click-middle = gnome-pomodoro
click-right = i3-gnome-pomodoro start_stop
exec = i3-gnome-pomodoro status --always
interval = 1

```

### waybar

I use the following module in waybar

config

```
 "custom/pomodoro": {
    "exec": "i3-gnome-pomodoro status --format=waybar --show-seconds",
     "return-type": "json",
     "interval": 1,
     "format": "Pomodoro {}",
     "on-click": "i3-gnome-pomodoro start",
     "on-click-middle": "i3-gnome-pomodoro toggle",
     "on-click-right": "i3-gnome-pomodoro stop",
 },

```

style.css

```css
#custom-pomodoro.paused {
  border-bottom: 3px solid @yellow;
}
```

### Refresh rate
i3-gnome-pomodoro displays a countdown timer on i3bar. If you use i3status, setting `resfresh_rate` in your i3status configuration can probably result in a better user experience. I personally use this configuration:

```
general {
    interval = 1
}
```

### Blinkstick

You can reflect your Pomodoro status on a Blinkstick by using the `--blinkstick` flag
in the status command.

### Keyboard shortcuts
I use the following key bindings in my i3 config:
```
bindsym $mod+F9 exec "~/repos/i3-gnome-pomodoro/pomodoro-client.py start"
bindsym $mod+F10 exec "~/repos/i3-gnome-pomodoro/pomodoro-client.py toggle"
bindsym $mod+F11 exec "~/repos/i3-gnome-pomodoro/pomodoro-client.py skip"
bindsym $mod+F12 exec "~/repos/i3-gnome-pomodoro/pomodoro-client.py stop"
```


### Suppressing dunst notifications and disabling workspaces
i3-gnome-pomodoro has a daemon that can suppress dunst notifications while a
pomodoro is active. After your pomodoro is over, dunst still delivers delayed
notifications. To use this daemon, launch it manually when needed or add this
to your i3 configuration to launch it on startup:

```
exec ~/repos/i3-gnome-pomodoro/pomodoro-client.py daemon &
```

If you want to disable any workspaces during your pomodoro, you can do so by
specifying there workspace number. For example, I generally use workspace 10
for IM, Social Media and Workspace 9 for email. Therefore I want them disabled
while I'm on a pomodoro. So, I execute my daemon like this:

```
exec ~/repos/i3-gnome-/pomodoro-client.py daemon 9 10 &
```

This works even if you label your workspaces. For example, I use the name "9: mail"
for my email workspace but I still reference it with "9".

I also like to have a nagbar warning shown when I still try to access a distracting workspace:

```
exec ~/repos/i3-gnome-/pomodoro-client.py daemon 9 10 --nagbar &
```
