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

async def Wait(seconds):
    target = time.time() + seconds
    while time.time() < target:
        if keyboard.is_pressed('p'):
            raise Error
        await asyncio.sleep(0.1)

@work(exit_on_error=False, exclusive=True)
async def prog(ctx, out):
    out.write_line("[prog] starting prog")
    ctx.monitoring = True
    ctx.query_one("#stats").update(f"Total refreshes: {ctx.num_refreshes}\nRefreshes/Min: {ctx.num_refreshes / (time.time() - ctx.app_start) * 60:.2f}\n")
    ctx.query_one("#status").update(f"{"Running" if ctx.monitoring else "Stopped"}")
    while True:
        await Wait(1)
        out.write_line("[prog] Checking the stuff")
        ctx.num_refreshes += 1
        ctx.query_one("#stats").update(f"Total refreshes: {ctx.num_refreshes}\nRefreshes/Min: {ctx.num_refreshes / (time.time() - ctx.app_start) * 60:.2f}\n")


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
    app_start = time.time()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            self.num_refreshes += 1
            self.query_one("#stats").update(f"{self.num_refreshes}")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR or event.state == WorkerState.CANCELLED:
            self.monitoring = False
            self.query_one("#stats").update(f"Total refreshes: {self.num_refreshes}\nRefreshes/Min: {self.num_refreshes / (time.time() - self.app_start) * 60:.2f}\n")
            self.query_one("#log").write_line("prog ended")
            self.query_one("#status-container").add_class("stopped")
            self.query_one("#status-container").remove_class("running")
            self.query_one("#status").update(f"{"Running" if self.monitoring else "Stopped"}")

    def on_input_submitted(self, event):
        text = self.query_one(Input)

        if text.value == "start" or text.value == "resume":
            if not self.monitoring:
                self.worker_handle = prog(self, self.query_one("#log"))
                self.query_one("#status-container").remove_class("stopped")
                self.query_one("#status-container").add_class("running")

        elif text.value == "stop" or text.value == "pause":
            self.worker_handle.cancel()

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
        self.worker_handle = prog(self, self.query_one("#log"))
        self.monitoring = True
        self.query_one(Input).focus()

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
