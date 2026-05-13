"""Demo application for cjm-fasthtml-file-browser library.

Showcases the virtualized file browser with:
1. General file browser (multi-select, all files)
2. Database file picker (extension filtering)

Run with: python demo_app.py
"""

from pathlib import Path


def main():
    """Initialize file browser demos and start the server."""
    from fasthtml.common import fast_app, Div, H1, H2, P, Span, A
    from cjm_fasthtml_app_core.core.routing import APIRouter

    from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
    from cjm_fasthtml_daisyui.core.testing import create_theme_persistence_script
    from cjm_fasthtml_daisyui.components.actions.button import btn, btn_colors, btn_sizes
    from cjm_fasthtml_daisyui.components.data_display.badge import badge, badge_colors
    from cjm_fasthtml_daisyui.components.data_display.card import card, card_body
    from cjm_fasthtml_daisyui.utilities.semantic_colors import bg_dui, text_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w, h
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.utilities.flexbox_and_grid import (
        grid_display, grid_cols, gap, flex_display, items, justify
    )
    from cjm_fasthtml_tailwind.utilities.borders import border, rounded
    from cjm_fasthtml_tailwind.utilities.layout import overflow
    from cjm_fasthtml_tailwind.core.base import combine_classes

    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    from cjm_fasthtml_file_browser.core.config import (
        FileBrowserConfig, FileBrowserCallbacks, FilterConfig, ViewConfig, SelectionMode, FileColumn
    )
    from cjm_fasthtml_file_browser.core.models import BrowserState
    from cjm_fasthtml_file_browser.providers.local import LocalFileSystemProvider
    from cjm_fasthtml_file_browser.routes.handlers import init_router

    from cjm_fasthtml_keyboard_navigation.components.hints_modal import render_keyboard_hints_modal

    print("\n" + "=" * 70)
    print("Initializing cjm-fasthtml-file-browser Demo")
    print("=" * 70)

    APP_ID = "fbrow"

    app, rt = fast_app(
        pico=False,
        hdrs=[*get_daisyui_headers(), create_theme_persistence_script()],
        title="File Browser Demo",
        htmlkw={'data-theme': 'light'},
        session_cookie=f'session_{APP_ID}_',
        secret_key=f'{APP_ID}-demo-secret',
    )
    router = APIRouter(prefix="")
    print("  FastHTML app created")

    # Provider
    provider = LocalFileSystemProvider()
    home_path = provider.get_home_path()
    print(f"  Home: {home_path}")

    # --- Demo 1: General file browser ---
    general_config = FileBrowserConfig(
        selection_mode=SelectionMode.MULTIPLE,
        selectable_types="both",
        show_path_bar=True,
        show_path_input=True,
        show_breadcrumbs=True,
        container_id="general-browser",
        content_id="general-browser-content",
        vc_prefix="gen",
    )

    # --- Demo 2: Database picker ---
    db_picker_config = FileBrowserConfig(
        selection_mode=SelectionMode.MULTIPLE,
        selectable_types="files",
        filter=FilterConfig(
            allowed_extensions=[".db", ".sqlite", ".sqlite3"],
            show_hidden=True,
        ),
        view=ViewConfig(
            columns=[FileColumn.NAME, FileColumn.SIZE, FileColumn.MODIFIED],
        ),
        container_id="db-picker-browser",
        content_id="db-picker-browser-content",
        vc_prefix="dbp",
    )

    # State
    browser_states = {
        "general": BrowserState(current_path=home_path),
        "db_picker": BrowserState(current_path=home_path),
    }

    def get_state(browser_id):
        def getter(): return browser_states[browser_id]
        return getter

    def set_state(browser_id):
        def setter(state): browser_states[browser_id] = state
        return setter

    # --- Selection display helpers ---
    def _render_selected_display(browser_id, label, selected_paths, oob=False):
        """Render the 'Selected' display for a browser demo."""
        display_id = f"{browser_id}-selected-display"
        text = ", ".join([Path(p).name for p in selected_paths]) or "None"
        attrs = {"id": display_id}
        if oob:
            attrs["hx_swap_oob"] = "true"
        return Div(
            Span(f"{label}: ", cls=font_weight.semibold),
            Span(text, cls=text_dui.base_content),
            cls=combine_classes(m.b(4), p(2), bg_dui.base_200, rounded()),
            **attrs,
        )

    def _make_selection_callback(browser_id, label):
        """Create an on_selection_change callback that returns OOB selected display."""
        def on_selection_change(selected_paths):
            return (_render_selected_display(browser_id, label, selected_paths, oob=True),)
        return on_selection_change

    # Routers — manager_label documents the new L7 plumbing. The label is
    # consumed by render_keyboard_hints_modal only when this router's kb_manager
    # is passed as a child_managers entry (hierarchical mode); single-manager
    # modals don't display it but setting it is harmless.
    general = init_router(
        config=general_config, provider=provider,
        state_getter=get_state("general"), state_setter=set_state("general"),
        route_prefix="/browser/general", home_path=home_path,
        callbacks=FileBrowserCallbacks(
            on_selection_change=_make_selection_callback("general", "Selected"),
        ),
        manager_label="General File Browser",
    )
    db_picker = init_router(
        config=db_picker_config, provider=provider,
        state_getter=get_state("db_picker"), state_setter=set_state("db_picker"),
        route_prefix="/browser/db_picker", home_path=home_path,
        callbacks=FileBrowserCallbacks(
            on_selection_change=_make_selection_callback("db_picker", "Selected databases"),
        ),
        manager_label="Database Picker",
    )
    print("  Created 2 browser routers")

    # --- Pages ---

    @router
    def index(request):
        def home_content():
            return Div(
                H1("File Browser Demo",
                   cls=combine_classes(font_size._4xl, font_weight.bold, m.b(4))),
                P("Virtualized file browser with keyboard navigation, sorting, and selection.",
                  cls=combine_classes(font_size.lg, text_dui.base_content, m.b(8))),

                Div(
                    # General browser card
                    Div(Div(
                        H2("General File Browser",
                           cls=combine_classes(font_size.xl, font_weight.semibold, m.b(2))),
                        P("Browse all files and directories with multi-select.",
                          cls=combine_classes(text_dui.base_content, m.b(4))),
                        Div(
                            Span("Multi-select", cls=combine_classes(badge, badge_colors.primary, m.r(2))),
                            Span("All files", cls=combine_classes(badge, badge_colors.accent)),
                            cls=m.b(4)
                        ),
                        A("Open Browser", href=demo_general.to(),
                          cls=combine_classes(btn, btn_colors.primary)),
                        cls=card_body
                    ), cls=combine_classes(card, bg_dui.base_200)),

                    # DB picker card
                    Div(Div(
                        H2("Database File Picker",
                           cls=combine_classes(font_size.xl, font_weight.semibold, m.b(2))),
                        P("Pick .db and .sqlite files.",
                          cls=combine_classes(text_dui.base_content, m.b(4))),
                        Div(
                            Span("Multi-select", cls=combine_classes(badge, badge_colors.primary, m.r(2))),
                            Span(".db/.sqlite", cls=combine_classes(badge, badge_colors.info)),
                            cls=m.b(4)
                        ),
                        A("Open Picker", href=demo_db_picker.to(),
                          cls=combine_classes(btn, btn_colors.secondary)),
                        cls=card_body
                    ), cls=combine_classes(card, bg_dui.base_200)),

                    cls=combine_classes(grid_display, grid_cols(1), grid_cols(2).md, gap(6), m.b(8))
                ),

                cls=combine_classes(container, max_w._6xl, m.x.auto, p(8), text_align.center)
            )
        return handle_htmx_request(
            request, home_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_general(request):
        def browser_content():
            state = browser_states["general"]
            # Keyboard shortcuts modal — single-manager mode, surfaces file-browser's
            # nav actions in the modal. Distinct modal_id per demo so the `?` listener
            # targets the right modal even though only one demo page renders at a time.
            hints_modal, hints_trigger, hints_script = render_keyboard_hints_modal(
                general.kb_manager,
                modal_id="fb-general-hints-modal",
            )
            return Div(
                Div(
                    Div(
                        H1("General File Browser",
                           cls=combine_classes(font_size._2xl, font_weight.bold)),
                        P("Click to focus, click again or Enter to navigate/select. Arrow keys to move.",
                          cls=combine_classes(text_dui.base_content, font_size.sm)),
                    ),
                    hints_trigger,
                    cls=combine_classes(flex_display, items.start, justify.between, m.b(4))
                ),
                _render_selected_display("general", "Selected", state.selection.selected_paths),
                Div(
                    general.render(),
                    cls=combine_classes(h(96), border(), rounded.lg, overflow.hidden)
                ),
                hints_modal,
                hints_script,
                cls=combine_classes(container, max_w._5xl, m.x.auto, p(6))
            )
        return handle_htmx_request(
            request, browser_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_db_picker(request):
        def browser_content():
            state = browser_states["db_picker"]
            hints_modal, hints_trigger, hints_script = render_keyboard_hints_modal(
                db_picker.kb_manager,
                modal_id="fb-db-picker-hints-modal",
            )
            return Div(
                Div(
                    Div(
                        H1("Database File Picker",
                           cls=combine_classes(font_size._2xl, font_weight.bold)),
                        P("Only .db, .sqlite, and .sqlite3 files shown. Multi-select enabled.",
                          cls=combine_classes(text_dui.base_content, font_size.sm)),
                    ),
                    hints_trigger,
                    cls=combine_classes(flex_display, items.start, justify.between, m.b(4))
                ),
                _render_selected_display("db_picker", "Selected databases", state.selection.selected_paths),
                Div(
                    db_picker.render(),
                    cls=combine_classes(h(96), border(), rounded.lg, overflow.hidden)
                ),
                hints_modal,
                hints_script,
                cls=combine_classes(container, max_w._5xl, m.x.auto, p(6))
            )
        return handle_htmx_request(
            request, browser_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    # Navbar
    navbar = create_navbar(
        title="File Browser Demo",
        nav_items=[
            ("Home", index),
            ("General", demo_general),
            ("DB Picker", demo_db_picker),
        ],
        home_route=index,
        theme_selector=True
    )

    # Register all routes (browser + collection routers for each demo)
    register_routes(
        app, router,
        general.browser, general.collection,
        db_picker.browser, db_picker.collection,
    )

    # Debug output
    print("\n" + "=" * 70)
    print("Registered Routes:")
    print("=" * 70)
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    print("=" * 70)
    print("Demo App Ready!")
    print("=" * 70 + "\n")

    return app


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    app = main()

    port = 5032
    host = "0.0.0.0"
    display_host = 'localhost' if host in ['0.0.0.0', '127.0.0.1'] else host

    print(f"Server: http://{display_host}:{port}")
    print(f"\n  http://{display_host}:{port}/              — Homepage")
    print(f"  http://{display_host}:{port}/demo_general  — General browser")
    print(f"  http://{display_host}:{port}/demo_db_picker — DB picker")
    print()

    timer = threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}"))
    timer.daemon = True
    timer.start()

    uvicorn.run(app, host=host, port=port)
