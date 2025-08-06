import typer
from nicegui import ui, app, events, native
import logging
import asyncio
from typing import Optional
from datetime import datetime
import cibutler.osdu as osdu
from cibutler._version import __version__
from rich.console import Console
# import httpx

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")

cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

diag_cli = typer.Typer(
    rich_markup_mode="rich", help="Community Implementation", no_args_is_help=True
)

# api = httpx.AsyncClient()
# running_query: Optional[asyncio.Task] = None
# results = []
# ui.markdown('This is **Markdown**.')
# ui.html('This is <strong>HTML</strong>.')
# ui.icon('thumb_up')

# with ui.button(icon='menu'):
#    with ui.menu():
#        ui.menu_item('Option 1')
#        ui.menu_item('Option 2')
#        with ui.menu_item('Option 3', auto_close=False):
#            with ui.item_section().props('side'):
#                ui.icon('keyboard_arrow_right')
#            with ui.menu().props('anchor="top end" self="top start" auto-close'):
#                ui.menu_item('Sub-option 1')
#                ui.menu_item('Sub-option 2')
#                ui.menu_item('Sub-option 3')


@ui.page("/page_layout1")
def page_layout1():
    with ui.header().classes(replace="row items-center") as header:
        ui.button(on_click=lambda: left_drawer.toggle(), icon="menu").props(
            "flat color=white"
        )
        with ui.tabs() as tabs:
            ui.tab("A")
            ui.tab("B")
            ui.tab("C")

    with ui.footer(value=False) as footer:
        ui.label("Footer")

    with ui.left_drawer().classes("bg-blue-100") as left_drawer:
        ui.label("Side menu")

    with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
        ui.button(on_click=footer.toggle, icon="contact_support").props("fab")

    with ui.tab_panels(tabs, value="A").classes("w-full"):
        with ui.tab_panel("A"):
            ui.label("Content of A")
        with ui.tab_panel("B"):
            ui.label("Content of B")
        with ui.tab_panel("C"):
            ui.label("Content of C")


@ui.page("/osdu")
# @ui.page('/{_:path}')
def osdu_page_layout():
    # [ui.label(f'Line {i}') for i in range(100)]
    result = ui.label().classes("mr-auto")
    with (
        ui.header(elevated=True)
        .style("background-color: #3874c8")
        .classes("items-center justify-between")
    ):
        with ui.button(icon="menu"):
            with ui.menu():
                ui.menu_item(
                    "Refresh Token",
                    on_click=lambda: ui.navigate.to("/osdu/refesh_token"),
                )
                ui.menu_item("Info", on_click=lambda: ui.navigate.to("/osdu/info"))
                ui.menu_item("Groups", on_click=lambda: ui.navigate.to("/osdu/groups"))
                ui.menu_item(
                    "Legal Tags", on_click=lambda: ui.navigate.to("/osdu/legal_tags")
                )
                # ui.menu_item("Search", on_click=lambda: ui.navigate.to("/osdu/search"))
        ui.label("CI Butler")
        ui.button("shutdown cibutler", on_click=app.shutdown)

    #    ui.button(on_click=lambda: right_drawer.toggle(), icon='menu').props('flat color=white')
    # with ui.left_drawer(top_corner=True, bottom_corner=True).style('background-color: #d7e3f4'):
    # ui.label('LEFT DRAWER')
    # with ui.right_drawer(fixed=False).style('background-color: #ebf1fa').props('bordered') as right_drawer:
    #    ui.label('RIGHT DRAWER')
    with ui.footer().style("background-color: #3874c8"):
        ui.label(f"CI Butler v{__version__}")
        ui.link("Docs", "https://osdu.pages.opengroup.org/ui/cibutler/")
        label = ui.label()
        ui.timer(1.0, lambda: label.set_text(f"{datetime.now():%X}"))


@ui.page("/osdu/info")
def osdu_info_page():
    with ui.row():
        ui.button("Back", on_click=ui.navigate.back)
        ui.button("Reload", on_click=ui.navigate.reload)
    with ui.card():
        ui.label("OSDU Endpoints Info")
        ui.code(osdu.get_info_all())


@ui.page("/osdu/groups")
def osdu_groups_page():
    with ui.row():
        ui.button("Back", on_click=ui.navigate.back)
        ui.button("Reload", on_click=ui.navigate.reload)
    with ui.card():
        ui.label("OSDU Groups")
        ui.code(osdu.groups())


@ui.page("/osdu/legal_tags")
def osdu_legal_tags_page():
    with ui.row():
        ui.button("Back", on_click=ui.navigate.back)
        ui.button("Reload", on_click=ui.navigate.reload)
    with ui.card():
        ui.label("OSDU Legal Tags")
        ui.code(osdu.legal_tags())


@ui.page("/osdu/refesh_token")
def osdu_refresh_token_page():
    with ui.row():
        ui.button("Back", on_click=ui.navigate.back)
        ui.button("Reload", on_click=ui.navigate.reload)
    with ui.card():
        ui.label("OSDU Refresh Token")
        ui.code(osdu.refresh_token())


"""
@ui.page('/osdu/search')
def osdu_search_page():
    with ui.row():
        ui.button('Back', on_click=ui.navigate.back)
        ui.button('Reload', on_click=ui.navigate.reload)
    with ui.card():
        ui.label("OSDU Search")
        # create a search field which is initially focused and leaves space at the top
        search_field = ui.input(on_change=lambda: e, search(results)) \
        .props('autofocus outlined rounded item-aligned input-class="ml-3"') \
        .classes('w-96 self-center mt-24 transition-all')
        results = ui.row()
"""


async def search(e: events.ValueChangeEventArguments, results) -> None:
    """Search for cocktails as you type."""
    global running_query  # pylint: disable=global-statement # noqa: PLW0603
    if running_query:
        running_query.cancel()  # cancel the previous query; happens when you type fast
    # search_field.classes('mt-2', remove='mt-24')  # move the search field up
    # results.clear()
    # store the http coroutine in a task so we can cancel it later if needed
    running_query = asyncio.create_task(
        api.get(f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={e.value}")
    )
    response = await running_query
    if response.text == "":
        return
    with results:  # enter the context of the results row
        for drink in (
            response.json()["drinks"] or []
        ):  # iterate over the response data of the api
            with ui.image(drink["strDrinkThumb"]).classes("w-64"):
                ui.label(drink["strDrink"]).classes(
                    "absolute-bottom text-subtitle2 text-center"
                )
    running_query = None


@diag_cli.command(rich_help_panel="CImpl Diagnostic Commands", hidden=True)
def webui():
    """
    Start the Experimental CIButler WebUI.
    """
    console.print("Starting CIButler WebUI...")
    ui.separator()
    ui.link("OSDU Actions", osdu_page_layout)
    app.on_startup(lambda: console.print("CIButler WebUI ready to go on ", app.urls))
    ui.run(
        host="127.0.0.1",
        port=native.find_open_port(),
        dark=True,
        favicon="🚀",
        reload=False,
        title="CIButler WebUI",
        show_welcome_message=False,
    )
