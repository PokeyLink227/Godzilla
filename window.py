from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Input
from textual.containers import Container
import time

class GodzillaApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "Quit Application")]

    num_refreshes = 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        if event.button.id == "start":
            self.num_refreshes += 1
            self.query_one("#stats").update(f"{self.num_refreshes}")


    def on_input_submitted(self, event):
        text = self.query_one(Input)
        self.query_one("#log").write_line(text.value)
        text.value = ""


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
        stats = Static(f"Total refreshes: {self.num_refreshes}\n\n", id="stats")
        stats.border_title = "Stats"
        input_area = Input(placeholder="Enter Command here", id="input-area")
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
                    Button("meow", id="start"),
                    id="buttons"
                ),
                id="bottom-row"
            ),
            id="content"
        )

if __name__ == "__main__":
    app = GodzillaApp()
    app.run()
