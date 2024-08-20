from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Placeholder
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

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Container(
            Container(
                Log("LOG", id="log"),
                Static("IGNORE", id="ignored-list"),
                Static("WATCH", id="watch-list"),
                id="top-row"
            ),
            Container(
                Static(f"{self.num_refreshes}", id="stats"),
                Static("INPUT", id="input-area"),
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
