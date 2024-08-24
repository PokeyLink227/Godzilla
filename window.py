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

@work(exit_on_error=False)
async def prog(ctx, out):
    out.write_line("[prog] starting prog")
    ctx.monitoring = True
    ctx.query_one("#stats").update(f"Total refreshes: {ctx.num_refreshes}\nMonitoring: {ctx.monitoring}\n")
    await asyncio.sleep(2)

    while True:
        await Wait(5)
        out.write_line("[prog] Checking the stuff")
        ctx.num_refreshes += 1
        ctx.query_one("#stats").update(f"Total refreshes: {ctx.num_refreshes}\nMonitoring: {ctx.monitoring}\n")


commands = [
    ("watch  ", "watch <Trip ID>"),
    ("unwatch  ", "unwatch <Trip ID>"),
    ("ignore  ", "ignore <Trip ID>"),
    ("unignore  ", "unignore <Trip ID>"),
    ("start", "start")
]

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            self.num_refreshes += 1
            self.query_one("#stats").update(f"{self.num_refreshes}")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            self.monitoring = False
            self.query_one("#stats").update(f"Total refreshes: {self.num_refreshes}\nMonitoring: {self.monitoring}\n")
            self.query_one(Log).write_line("prog ended")

    def on_input_submitted(self, event):
        text = self.query_one(Input)
        if text.value == "start":
            prog(self, self.query_one(Log))
            None
        elif text.value == "quit":
            self.query_one("#log").write_line(text.value)
            self.exit()

        self.query_one("#log").write_line(text.value)
        text.value = ""

    def on_mount(self):
        prog(self, self.query_one(Log))
        self.query_one(Input).focus()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        log = Log("LOG", id="log")
        log.border_title = "Program Log"
        ignore = Static("IGNORE", id="ignored-list")
        ignore.border_title = "Ignored"
        watch = Static("WATCH", id="watch-list")
        watch.border_title = "Watch List"
        stats = Static(f"Total refreshes: {self.num_refreshes}\nMonitoring: {self.monitoring}\n", id="stats")
        stats.border_title = "Stats"
        input_area = Input(
            placeholder="Enter Command here",
            suggester=AutoCompletion(),
            id="input-area")
        input_area.border_title = "Input"

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
                Container(
                    #Button("meow", id="start"),
                    id="buttons"
                ),
                id="bottom-row"
            ),
            id="content"
        )

if __name__ == "__main__":
    app = GodzillaApp()
    app.run()
