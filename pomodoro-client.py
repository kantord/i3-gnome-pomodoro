#!/usr/bin/env python3

from gi.repository import GLib
from pydbus import SessionBus
from subprocess import Popen
from threading import Thread
import click
import i3ipc
import math
import os


bus = SessionBus()

           
def get_notification_proxy():
    return bus.get(
        "org.freedesktop.Notifications", "/org/freedesktop/Notifications")


def get_pomodoro_proxy():
    return bus.get("org.gnome.Pomodoro", "/org/gnome/Pomodoro")


def format_time(seconds, show_seconds):
    time = "{minutes:02d}".format(minutes=int(math.floor(round(seconds)/60))) + (
        ":{seconds:02d}".format(seconds=int(round(seconds) % 60)) if show_seconds
        else "m"
    )

    return time


def format_is_paused(is_paused, format):
    if format == 'waybar':
        return "paused" if is_paused else ""
    return " PAUSED " if is_paused else ""


def format_state(state, icon_text):
    return {
        "pomodoro": icon_text,
        "short-break": "Break",
        "long-break": "Long Break",
    }[state]


def extract_pomodoro_data(pomodoro):
    return {
        "elapsed": pomodoro.Elapsed, "is_paused": pomodoro.IsPaused,
        "duration": pomodoro.StateDuration,
        "remaining": pomodoro.StateDuration - pomodoro.Elapsed,
        "state": pomodoro.State
    }


def format_pomodoro_data(pomodoro_data, icon_text, show_seconds, format):
    return {
        "elapsed": format_time(pomodoro_data["elapsed"], show_seconds),
        "duration": format_time(pomodoro_data["duration"], show_seconds),
        "remaining": format_time(pomodoro_data["remaining"], show_seconds),
        "is_paused": format_is_paused(pomodoro_data["is_paused"], format),
        "state": format_state(pomodoro_data["state"], icon_text),
    }


def format_output_text(pomodoro_data, always, icon_text, show_seconds, format):

    if pomodoro_data["state"] != "null":
        return "{state} {remaining} {is_paused}".format(**format_pomodoro_data(
            pomodoro_data, icon_text, show_seconds, format
        ))
    if always:
        return icon_text
    return ""


def format_output_waybar(pomodoro_data, always, icon_text, show_seconds, format):
    import json

    output = {"class": "stopped", "text": "", "tooltip": ""}
    if pomodoro_data["state"] != "null":
        if icon_text != "":
            icon_text = icon_text + " "
        data = format_pomodoro_data(pomodoro_data, icon_text, show_seconds, format)
        output["class"] = data["is_paused"]
        output["text"] = "{}{}".format(icon_text, data["remaining"])
        output["tooltip"] = "Elapsed: {}\nRemaining: {}".format(
            data["elapsed"], data["remaining"]
        )
        return json.dumps(output)
    if always:
        output['text'] = icon_text
        return json.dumps(output)


def format_output(pomodoro_data, always, icon_text, show_seconds, format="text"):

    if pomodoro_data["state"] != "null":
        return "{state} {remaining} {is_paused}".format(**format_pomodoro_data(
            pomodoro_data, icon_text, show_seconds, format
        ))
    if always:
        return icon_text
    return ""


def detect_nagbar():
    with open(os.devnull, "w") as devnull:
        if subprocess.call(["pgrep", "i3"], stdout=devnull) == 0:
            return "i3-nagbar"
        else:
            return "swaynag"


@click.group()
def main():
    pass

@click.option('--always/--not-always', default=False,
              help="""Show a constant icon.""")
@click.option('--show-seconds/--no-seconds', default=True,
              help="""Show seconds in timers""")
@click.option('--icon-text', default="Pomodoro", help='What to show as icon.')
@click.option("--format", default="text", help="""Output format, 'text' or 'waybar', default 'text'""")
@click.command(help=
               """
               Returns a string descriping the current pomodoro state.
               """)
def status(always, icon_text, show_seconds, format):
    pomodoro = get_pomodoro_proxy()
    pomodoro_data = extract_pomodoro_data(pomodoro)
    if format == 'waybar':
        click.echo(format_output_waybar(pomodoro_data, always, icon_text, show_seconds, format))
    else:
        click.echo(format_output_text(pomodoro_data, always, icon_text, show_seconds, format))


@click.command(help="""Pauses the current pomodoro if any is running.""")
def pause():
    get_pomodoro_proxy().Pause()


@click.command(help="""Resume pomodoro if paused.""")
def resume():
    get_pomodoro_proxy().Resume()


@click.command(help="Start a pomodoro.")
def start():
    get_pomodoro_proxy().Start()


@click.command(help="Stop current pomodoro.")
def stop():
    get_pomodoro_proxy().Stop()

@click.command(help="Toggling function to start a pomodoro if none is running or stop the current one.")
def start_stop():
    pomodoro = get_pomodoro_proxy()
    if pomodoro.State == 'null':
        pomodoro.Start()
    elif pomodoro.State == 'pomodoro':
        pomodoro.Stop()


@click.command(help="Skip the current activity.")
def skip():
    get_pomodoro_proxy().Skip()


@click.command()
def reset(help="Reset the current pomodoro."):
    get_pomodoro_proxy().Reset()


@click.command()
def toggle(help="Toggling function to pause/resume current pomodoro."):
    pomodoro = get_pomodoro_proxy()
    if pomodoro.IsPaused:
        pomodoro.Resume()
    else:
        pomodoro.Pause()


def dunst_action(action):
    notify = get_notification_proxy()
    notify.Notify("", 0, "", action, "", "", "", 0)


def stop_dunst():
    dunst_action("DUNST_COMMAND_PAUSE")


def start_dunst():
    dunst_action("DUNST_COMMAND_RESUME")


def handle_state(state, old_state):
    if state["name"] == "pomodoro":
        stop_dunst()
    else:
        start_dunst()


def show_message(message, is_error=False):
    type_ = "error" if is_error else "warning"
    Popen('%s -t %s -m "%s"' % (detect_nagbar(), type_, message), shell=True)


def get_focused_workspace(i3):
    return i3.get_tree().find_focused().workspace()


def create_workspace_policy(disabled_during_pomodoro):
    def allowed_workspace(number):
        pomodoro = get_pomodoro_proxy()
        if pomodoro.State == "pomodoro" and pomodoro.IsPaused == False:
            return number not in disabled_during_pomodoro
        else:
            return True

    return allowed_workspace


def activate_workspace(i3, name):
    i3.command("workspace %s" % name)


def handle_workspace_focus(i3, i3_state, allowed_workspace, nagbar):
    def handler(self, e):
        if not allowed_workspace(e.current.num):
            activate_workspace(i3, i3_state["focused_workspace_name"])
            if nagbar:
                show_message("Workspace %s is not allowed during a pomodoro"
                             % e.current.name)
        i3_state["focused_workspace_name"] = e.current.name

    return handler


def i3_daemon(disabled_during_pomodoro, nagbar):
    def generated_daemon():
        workspace_policy = create_workspace_policy(disabled_during_pomodoro)
        i3 = i3ipc.Connection()
        i3_state = {
            "focused_workspace_name": get_focused_workspace(i3).name
        }
        i3.on('workspace::focus', handle_workspace_focus(
            i3, i3_state, workspace_policy, nagbar))
        i3.main()

    return generated_daemon


def pomodoro_daemon():
    pomodoro = get_pomodoro_proxy()
    pomodoro.StateChanged.connect(handle_state)
    GLib.MainLoop().run()


@click.command(help="Disable certain workspaces during pomodoro")
@click.argument('workspaces_disabled_during_pomodoro', nargs=-1, type=int)
@click.option('--nagbar/--no-nagbar', default=False)
def daemon(workspaces_disabled_during_pomodoro, nagbar):
    daemon_commands = [
        i3_daemon(workspaces_disabled_during_pomodoro, nagbar), pomodoro_daemon]
    threads = [Thread(target=command) for command in daemon_commands]
    for thread in threads:
        thread.daemon = True
        thread.start()

    for thread in threads:
        thread.join()


main.add_command(status)
main.add_command(pause)
main.add_command(resume)
main.add_command(start)
main.add_command(stop)
main.add_command(start_stop)
main.add_command(skip)
main.add_command(reset)
main.add_command(toggle)
main.add_command(daemon)

if __name__ == "__main__":
    main()
