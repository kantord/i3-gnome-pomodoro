#!/usr/bin/env python

import math
from threading import Thread
from subprocess import Popen
from pydbus import SessionBus
from gi.repository import GLib
import click
import i3ipc


bus = SessionBus()


def get_notification_proxy():
    return bus.get(
        "org.freedesktop.Notifications", "/org/freedesktop/Notifications")


def get_pomodoro_proxy():
    try:
        return bus.get("org.gnome.Pomodoro", "/org/gnome/Pomodoro")
    except GLib.Error:
        return None


def format_time(seconds):
    return "{minutes:02d}:{seconds:02d}".format(
        minutes=int(math.floor(seconds / 60)),
        seconds=int(round(seconds % 60))
    )


def format_is_paused(is_paused):
    return " PAUSED " if is_paused else ""


def format_state(state):
    return {
        "pomodoro": "Pomodoro",
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


def format_pomodoro_data(pomodoro_data):
    return {
        "elapsed": format_time(pomodoro_data["elapsed"]),
        "duration": format_time(pomodoro_data["duration"]),
        "remaining": format_time(pomodoro_data["remaining"]),
        "is_paused": format_is_paused(pomodoro_data["is_paused"]),
        "state": format_state(pomodoro_data["state"]),
    }


def format_output(pomodoro_data):
    if pomodoro_data["state"] != "null":
        return "{state} {remaining} {is_paused}".format(**format_pomodoro_data(
            pomodoro_data
        ))
    else:
        return ""


@click.group()
def main():
    pass

def command_with_pomodoro_proxy(nagbar):
    def wrapper(cmd):
        def command_wrapper(pomodoro):
            pomodoro = get_pomodoro_proxy()
            if pomodoro is not None:
                cmd(pomodoro)
            else:
                if nagbar:
                    show_message("(i3-gnome-pomodoro) Error: gnome-pomodoro is not running", is_error=True)
                click.echo("")
        return command_wrapper
    return wrapper


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def status(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_status(pomodoro):
        pomodoro_data = extract_pomodoro_data(pomodoro)
        click.echo(format_output(pomodoro_data))
    run_status(None)

@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def pause(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_pause(pomodoro):
        pomodoro.Pause()
    run_pause(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def resume(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_resume(pomodoro):
        pomodoro.Resume()
    run_resume(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def start(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_start(pomodoro):
        pomodoro.Start()
    run_start(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def stop(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_stop(pomodoro):
        pomodoro.Stop()
    run_stop(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def skip(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_skip(pomodoro):
        pomodoro.Skip()
    run_skip(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def reset(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_reset(pomodoro):
        pomodoro.Reset()
    run_reset(None)


@click.command()
@click.option('--nagbar/--no-nagbar', default=False)
def toggle(nagbar):
    @command_with_pomodoro_proxy(nagbar)
    def run_toggle(pomodoro):
        if pomodoro.IsPaused:
            pomodoro.Resume()
        else:
            pomodoro.Pause()
    run_toggle(None)


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
    Popen('i3-nagbar -t %s -m "%s"' % (type_, message), shell=True)

def get_focused_workspace(i3):
    return i3.get_tree().find_focused().workspace()


def create_workspace_policy(disabled_during_pomodoro):
    def allowed_workspace(number):
        pomodoro = get_pomodoro_proxy()
        if pomodoro is None:
            return True

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


@click.command()
@click.argument('workspaces_disabled_during_pomodoro', nargs=-1, type=int)
@click.option('--nagbar/--no-nagbar', default=False)
def daemon(workspaces_disabled_during_pomodoro, nagbar):
    daemon_commands = [
        i3_daemon(workspaces_disabled_during_pomodoro, nagbar), pomodoro_daemon]
    threads = [Thread(target=command) for command in daemon_commands]
    for thread in threads:
        thread.daemon=True
        thread.start()

    for thread in threads:
        thread.join()

main.add_command(status)
main.add_command(pause)
main.add_command(resume)
main.add_command(start)
main.add_command(stop)
main.add_command(skip)
main.add_command(reset)
main.add_command(toggle)
main.add_command(daemon)

if __name__ == "__main__":
    main()
