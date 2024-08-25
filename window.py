from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Input
from textual.containers import Container
from textual.suggester import SuggestFromList, Suggester
from textual import work
from textual.worker import Worker, WorkerState
import time
import asyncio

import keyboard
import pyautogui

import win32gui
import re

# GLOBALS
VERSION = 'v2.0.5'

# FUNCTIONS

async def Wait(seconds):
    target = time.time() + seconds
    while time.time() < target:
        if keyboard.is_pressed('p'):
            raise Error
        await asyncio.sleep(0.1)

@work(exit_on_error=False, exclusive=True)
async def update(app, log):
    log.write_line(f'Checking for updates')
    return

    url = "https://api.github.com/repos/pokeylink227/godzilla/releases/latest"
    response = requests.get(url)

    if response.json()['tag_name'] > VERSION:
        log.write_line('Update found')
        r = requests.get(response.json()['assets'][0]['browser_download_url'])
        f = open('update.zip','wb')
        f.write(r.content)
        f.close()

        dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

        if os.path.exists(f'{dir}\\temp'):
            shutil.rmtree(f'{dir}\\temp')

        with ZipFile('update.zip') as zpf:
            zpf.extractall()

        shutil.move(f'{dir}\\main\\main', f'{dir}\\temp')

        f = open(f'{dir}/upd.bat', 'w')
        f.write(f'@echo off  \ncd {dir}\nrmdir /s /q {dir}\\main  \ntimeout 2 >nul\nrename {dir}\\temp main  \ntimeout 2 >nul\ndel {dir}\\upd.bat') #add absolute paths
        f.close()
        os.startfile(f'{dir}/upd.bat')

        sys.exit()
    log.write_line('Program up to date')

@work(exit_on_error=False, exclusive=True)
async def prog(app, out):
    out.write_line("Monitoring Started")
    out.write_line("Waiting 10 Sec")
    app.monitoring = True
    await asyncio.sleep(10)

    app.query_one("#stats").update(f"Total refreshes: {app.num_refreshes}\nRefreshes/Min: {app.num_refreshes / (time.time() - app.app_start) * 60:.2f}\n")
    while True:
        await Wait(1)
        out.write_line("[prog] Checking the stuff")
        app.num_refreshes += 1
        app.query_one("#stats").update(f"Total refreshes: {app.num_refreshes}\nRefreshes/Min: {app.num_refreshes / (time.time() - app.app_start) * 60:.2f}\n")


commands = [
    ("watch  ", "watch <Trip ID>"),
    ("unwatch  ", "unwatch <Trip ID>"),
    ("ignore  ", "ignore <Trip ID>"),
    ("unignore  ", "unignore <Trip ID>"),
    ("start", "start"),
    ("resume", "resume"),
    ("stop", "stop"),
    ("pause", "pause"),
    ("quit", "quit")
]

ignored = [
]

watch_list = []

class AutoCompletion(Suggester):
    async def get_suggestion(self, value: str):
        for pat, txt in commands:
            if value.startswith(pat[:(min(len(pat), len(value)))]):
                return txt
        return None

class GodzillaApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "Quit Application")]

    num_refreshes = 0
    monitoring = False
    worker_handle = None
    updater = None
    app_start = time.time()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            self.num_refreshes += 1
            self.query_one("#stats").update(f"{self.num_refreshes}")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker == self.worker_handle:
            if event.state == WorkerState.ERROR or event.state == WorkerState.CANCELLED:
                self.monitoring = False
                self.query_one("#stats").update(f"Total refreshes: {self.num_refreshes}\nRefreshes/Min: {self.num_refreshes / (time.time() - self.app_start) * 60:.2f}\n")
                self.query_one("#log").write_line("Monitoring Stopped")
                self.query_one("#status-container").remove_class("running")
                self.query_one("#status-container").add_class("stopped")
                self.query_one("#status").update(f"{"Running" if self.monitoring else "Stopped"}")

        elif event.worker == self.updater:
            if event.state == WorkerState.SUCCESS:
                self.worker_handle = prog(self, self.query_one("#log"))
                self.monitoring = True
                self.query_one("#status-container").remove_class("stopped")
                self.query_one("#status-container").add_class("running")
                self.query_one("#status").update(f"{"Running" if app.monitoring else "Stopped"}")

            elif event.state == WorkerState.ERROR:
                self.panic("[red]Error: [white]Update failed, Check internet connection")

    def on_input_submitted(self, event):
        text = self.query_one(Input)

        if text.value == "start" or text.value == "resume":
            if not self.monitoring:
                self.worker_handle = prog(self, self.query_one("#log"))
                self.query_one("#status-container").remove_class("stopped")
                self.query_one("#status-container").add_class("running")
                self.query_one("#status").update(f"{"Running" if app.monitoring else "Stopped"}")

        elif text.value == "stop" or text.value == "pause":
            self.worker_handle.cancel()
            self.query_one("#status-container").remove_class("running")
            self.query_one("#status-container").add_class("stopped")

        elif text.value[:7] == "ignore ":
            ignored.append(text.value[7:])
            self.query_one("#ignored-list").update(f"{'\n'.join(ignored)}")

        elif text.value[:9] == "unignore ":
            if text.value[9:] in ignored:
                ignored.remove(text.value[9:])
            self.query_one("#ignored-list").update(f"{'\n'.join(ignored)}")

        elif text.value[:6] == "watch ":
            watch_list.append(text.value[6:])
            self.query_one("#watch-list").update(f"{'\n'.join(watch_list)}")

        elif text.value[:8] == "unwatch ":
            if text.value[8:] in watch_list:
                watch_list.remove(text.value[8:])
            self.query_one("#watch-list").update(f"{'\n'.join(watch_list)}")

        elif text.value == "quit":
            self.query_one("#log").write_line(text.value)
            self.exit()

        text.value = ""

    def on_mount(self):
        self.title = "Godzilla"
        self.sub_title = VERSION
        self.updater = update(self, self.query_one("#log"))
        self.query_one(Input).focus()
        self.query_one("#status-container").add_class("stopped")


    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        log = Log("LOG", id="log")
        log.border_title = "Program Log"
        ignore = Static(f"{'\n'.join(ignored)}", id="ignored-list")
        ignore.border_title = "Ignored"
        watch = Static("WATCH", id="watch-list")
        watch.border_title = "Watch List"
        stats = Static(f"Total refreshes: {self.num_refreshes}\nRefreshes/Min: {self.num_refreshes / (time.time() - self.app_start) * 60:.2f}\n", id="stats")
        stats.border_title = "Stats"
        input_area = Input(
            placeholder="Enter Command here",
            suggester=AutoCompletion(),
            id="input-area")
        input_area.border_title = "Input"
        status = Static(f"{"Running" if self.monitoring else "Stopped"}", id="status")
        status_container = Container(status, id="status-container")
        status_container.add_class("running")

        yield Container(
            Container(
                log,
                ignore,
                watch,
                id="top-row"
            ),
            Container(
                stats,
                input_area,
                status_container,
                id="bottom-row"
            ),
            id="content"
        )

if __name__ == "__main__":
    app = GodzillaApp()
    app.run()
