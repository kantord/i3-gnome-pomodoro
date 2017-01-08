import math
from pydbus import SessionBus
import click


def get_pomodoro_proxy():
    return SessionBus().get("org.gnome.Pomodoro", "/org/gnome/Pomodoro")


def format_time(seconds):
    return "{minutes:02d}:{seconds:02d}".format(
        minutes=math.floor(seconds / 60),
        seconds=round(seconds % 60)
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


@click.command()
def status():
    pomodoro = get_pomodoro_proxy()
    pomodoro_data = extract_pomodoro_data(pomodoro)
    click.echo(format_output(pomodoro_data))


@click.command()
def pause():
    get_pomodoro_proxy().Pause()


@click.command()
def resume():
    get_pomodoro_proxy().Resume()


@click.command()
def start():
    get_pomodoro_proxy().Start()


@click.command()
def skip():
    get_pomodoro_proxy().Skip()


@click.command()
def reset():
    get_pomodoro_proxy().Reset()


main.add_command(status)
main.add_command(pause)
main.add_command(resume)
main.add_command(start)
main.add_command(skip)
main.add_command(reset)

if __name__ == "__main__":
    main()
