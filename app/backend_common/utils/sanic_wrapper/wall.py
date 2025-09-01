"""The Torpedo 'Wall'.

Author: Lakshay Bansal <lakshay.bansal@1mg.com>
"""

import platform

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from sanic import Sanic

from app.backend_common.utils.sanic_wrapper.utils import is_atty, is_local

LOGO_1MG = """
     ▓▓▓ █████████████████████████     
  ▓▓▓██▓   ▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒▒▒▒▒    
    ▒██▓ ███████████████  █████████▒   
    ▒██▓ ███   ███   ███ ▓██▒   ███▒   
    ▒██▓ ███   ███   ███ ▓██▓▒ ▒███▒   
    ▒██▓ ███   ███   ███  ▒████████▒   
    ▒▒▒▒ ▒▒▒   ▒▒▒   ▒▒▒        ███     
     ███████████████████  ████████▒     
"""  # noqa

LOGO_TORPEDO = """


▀█▀ █▀█ █▀█ █▀█ █▀▀ █▀▄ █▀█   █░█ █░█
░█░ █▄█ █▀▄ █▀▀ ██▄ █▄▀ █▄█   ▀▄▀ ▀▀█

        Going Fast with [bold reverse red]Sanic[/bold reverse red]

"""  # noqa


COLOR_1MG = "#fe6f61"


class Wall:
    """The Torpedo Wall.

    To Render torpedo banner and app meta info.

    Author:
        Lakshay Bansal <lakshay.bansal@1mg.com>
    """

    def __init__(self, app: Sanic):
        self.app: Sanic = app
        self.console: Console = Console()

    def render(self) -> None:
        # SAFEGUARD!
        if not is_local() or not is_atty():
            return

        self.console.print(self.group())

    def group(self) -> Group:
        return Group(
            *[
                self._err_handlers(),
                self._routes(),
                self._banner(),
                self._meta_info(),
            ]
        )

    def _err_handlers(self) -> Panel:
        table = Table(
            box=box.SIMPLE,
            width=80,
            row_styles=["none", "dim"],
        )
        table.add_column("Exception", justify="left", style="bold #fe6f61 reverse")
        table.add_column("Handler", style="bold white")
        table.add_column("Route", justify="right", style="bold gray66")

        for (err, route), handler in self.app.error_handler.cached_handlers.items():
            route = route or "ALL"
            table.add_row(err.__name__, handler.__name__, Text(route, overflow="ellipsis"))

        return Panel(table, expand=False, title="Error Handlers")

    def _routes(self) -> Panel:
        bp_table = Table(
            box=box.SIMPLE,
            width=80,
            leading=1,
            padding=0,
            row_styles=["none", "dim"],
        )
        bp_table.add_column(header="Blueprint", style="bold white", no_wrap=True)
        bp_table.add_column(header="Routes")

        for name, bp in self.app.blueprints.items():
            route_table = Table(
                show_edge=False,
                show_header=False,
                expand=False,
                row_styles=["", "dim"],
                box=box.MINIMAL,
            )

            for route in bp.routes:
                route_table.add_row(f"/{route.path}", style="bold blue reverse")

            bp_table.add_row(Text(name, style="bold blue"), route_table)

        return Panel(bp_table, title="Blueprints", expand=False)

    def _banner(self):
        t = Table(
            box=box.SIMPLE,
            # width=80,
            row_styles=["none", "dim"],
            show_header=False,
            pad_edge=False,
        )

        t.add_column(style="bold", no_wrap=True)
        t.add_column()

        t.add_row(Text(LOGO_1MG, style="reverse #fe6f61"), LOGO_TORPEDO)

        return Panel(t, expand=False, box=box.HORIZONTALS, padding=0, border_style="bold #fe6f61")

    def _meta_info(self):
        host_config = self.app.ctx.host_config

        DEBUG = "[green]ON" if host_config.DEBUG else "[yellow]OFF"

        if host_config.WORKERS == 1 and host_config.SINGLE_PROCESS:
            SINGLE_PROCESS = "[green]ON"
        else:
            SINGLE_PROCESS = "[yellow]OFF"

        if host_config.HOST:
            host = host_config.HOST
        else:
            host = "localhost"

        t = Table(
            box=box.SIMPLE,
            show_header=False,
            # row_styles=["none", "dim"],
            width=80,
            # leading=1,
        )

        t.add_column(style="bold")
        t.add_column(style="bold", justify="right")

        t.add_row("[bold white on red]DEBUG[/bold white on red] Mode", DEBUG)
        t.add_row(
            "[bold white on blue]SINGLE PROCESS[/bold white on blue] Mode",
            SINGLE_PROCESS,
        )
        t.add_section()
        t.add_row(
            "[bold white][red]☵[/red] running",
            f"[blue]http://{host}:{host_config.PORT}/",
        )
        t.add_row("[bold white][red]☵[/red] service", f"{self.app.name}")
        t.add_row(
            "[bold white][red]☵[/red] workers",
            Text(f"{self.app.config.get('WORKERS')}"),
        )
        t.add_section()
        t.add_row("[bold white][red]☵[/red] python", f"[bold blue]{platform.python_version()}")
        t.add_row("[bold white][red]☵[/red] sanic", "[bold green]23.12.2")  # HARDCODED
        t.add_row("[bold white][red]☵[/red] sanic-ext", "[bold green]23.12.0")  # HARDCODED
        t.add_row("[bold white][red]☵[/red] sanic-routing", "[bold green]23.12.0")  # HARDCODED

        return Panel(t, expand=False, box=box.SIMPLE, highlight=True)
