"""Demo application for cjm-fasthtml-file-browser library.

This demo showcases the file browser component:

1. LocalFileSystemProvider:
   - Interactive directory navigation
   - File metadata extraction with type detection
   - Path validation and normalization

2. FileBrowserConfig:
   - Selection modes (none, single, multiple)
   - View modes (list, grid)
   - Extension filtering
   - Customizable columns and sorting

3. HTMX Integration:
   - Partial page updates for smooth navigation
   - Keyboard-ready component IDs
   - State persistence across interactions

4. Component Hierarchy:
   - Path bar with breadcrumbs and navigation buttons
   - Toolbar with view toggle and sort controls
   - Directory listing with file/folder items
   - Selection state tracking

Run with: python demo_app.py
"""

from pathlib import Path


def main():
    """Main entry point - initializes file browser and starts the server."""
    from fasthtml.common import fast_app, Div, H1, H2, P, Span, A, Code, Script, APIRouter

    # DaisyUI and Tailwind utilities
    from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
    from cjm_fasthtml_daisyui.core.testing import create_theme_persistence_script
    from cjm_fasthtml_daisyui.components.actions.button import btn, btn_colors, btn_sizes
    from cjm_fasthtml_daisyui.components.data_display.badge import badge, badge_colors
    from cjm_fasthtml_daisyui.components.data_display.card import card, card_body
    from cjm_fasthtml_daisyui.utilities.semantic_colors import bg_dui, text_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w, w, h, min_h
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.utilities.flexbox_and_grid import (
        flex_display, flex_direction, items, justify, grid_display, grid_cols, gap
    )
    from cjm_fasthtml_tailwind.utilities.borders import border, rounded
    from cjm_fasthtml_tailwind.utilities.layout import overflow
    from cjm_fasthtml_tailwind.core.base import combine_classes

    # App core utilities
    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    # File browser components
    from cjm_fasthtml_file_browser.core.config import (
        FileBrowserConfig, FilterConfig, ViewConfig, SelectionMode, ViewMode, FileColumn
    )
    from cjm_fasthtml_file_browser.core.models import BrowserState, BrowserSelection
    from cjm_fasthtml_file_browser.providers.local import LocalFileSystemProvider
    from cjm_fasthtml_file_browser.components.browser import render_file_browser, generate_scroll_preservation_script
    from cjm_fasthtml_file_browser.routes.handlers import init_router

    print("\n" + "=" * 70)
    print("Initializing cjm-fasthtml-file-browser Demo")
    print("=" * 70)

    # Create the FastHTML app
    app, rt = fast_app(
        pico=False,
        hdrs=[
            *get_daisyui_headers(),
            create_theme_persistence_script(),
        ],
        title="File Browser Demo",
        htmlkw={'data-theme': 'light'},
        secret_key="demo-secret-key"
    )

    router = APIRouter(prefix="")

    print("  FastHTML app created successfully")

    # Create the file system provider
    print("\n[1/3] Creating LocalFileSystemProvider...")
    provider = LocalFileSystemProvider()
    home_path = provider.get_home_path()
    print(f"  Home directory: {home_path}")

    # Create browser configurations for different demos
    print("\n[2/3] Creating browser configurations...")

    # Demo 1: General file browser (default config)
    general_config = FileBrowserConfig(
        selection_mode=SelectionMode.MULTIPLE,
        selectable_types="both",
        show_path_bar=True,
        show_path_input=True,
        show_breadcrumbs=True,
        show_toolbar=True,
        container_id="general-browser",
        content_id="general-browser-content",
        path_bar_id="general-browser-path",
        listing_id="general-browser-listing",
    )

    # Demo 2: Database file picker (.db files only)
    db_picker_config = FileBrowserConfig(
        selection_mode=SelectionMode.MULTIPLE,
        selectable_types="files",
        filter=FilterConfig(
            allowed_extensions=[".db", ".sqlite", ".sqlite3"],
            show_hidden=True,
        ),
        view=ViewConfig(
            default_mode=ViewMode.LIST,
            columns=[FileColumn.NAME, FileColumn.SIZE, FileColumn.MODIFIED],
        ),
        container_id="db-picker-browser",
        content_id="db-picker-browser-content",
        path_bar_id="db-picker-browser-path",
        listing_id="db-picker-browser-listing",
    )

    # Demo 3: Image gallery browser
    image_config = FileBrowserConfig(
        selection_mode=SelectionMode.SINGLE,
        selectable_types="files",
        filter=FilterConfig(
            allowed_extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
            show_hidden=False,
        ),
        view=ViewConfig(
            default_mode=ViewMode.GRID,
            grid_columns=4,
            show_thumbnails=True,
        ),
        container_id="image-browser",
        content_id="image-browser-content",
        path_bar_id="image-browser-path",
        listing_id="image-browser-listing",
    )

    print("  Created 3 browser configurations:")
    print("    - General file browser (multi-select, all files)")
    print("    - Database picker (.db/.sqlite files only)")
    print("    - Image browser (grid view, image files only)")

    # State management using session storage
    # In a real app, you'd use a proper state store
    browser_states = {
        "general": BrowserState(current_path=home_path),
        "db_picker": BrowserState(current_path=home_path),
        "image": BrowserState(current_path=home_path, view_mode="grid"),
    }

    def get_state(browser_id: str):
        def getter():
            return browser_states[browser_id]
        return getter

    def set_state(browser_id: str):
        def setter(state: BrowserState):
            browser_states[browser_id] = state
        return setter

    # Create routers for each browser
    print("\n[3/3] Creating browser routers...")

    general_browser_router = init_router(
        config=general_config,
        provider=provider,
        state_getter=get_state("general"),
        state_setter=set_state("general"),
        route_prefix="/browser/general",
        home_path=home_path,
    )

    db_picker_browser_router = init_router(
        config=db_picker_config,
        provider=provider,
        state_getter=get_state("db_picker"),
        state_setter=set_state("db_picker"),
        route_prefix="/browser/db_picker",
        home_path=home_path,
    )

    image_browser_router = init_router(
        config=image_config,
        provider=provider,
        state_getter=get_state("image"),
        state_setter=set_state("image"),
        route_prefix="/browser/image",
        home_path=home_path,
    )

    print("  Created 3 browser routers")

    # Define page routes
    @router
    def index(request):
        """Homepage with demo overview."""

        def home_content():
            return Div(
                H1("File Browser Demo",
                   cls=combine_classes(font_size._4xl, font_weight.bold, m.b(4))),

                P("Interactive file system navigation UI for FastHTML applications.",
                  cls=combine_classes(font_size.lg, text_dui.base_content, m.b(8))),

                # Feature cards
                Div(
                    # General browser card
                    Div(
                        Div(
                            H2("General File Browser",
                               cls=combine_classes(font_size.xl, font_weight.semibold, m.b(2))),
                            P("Browse all files and directories with multi-select support.",
                              cls=combine_classes(text_dui.base_content, m.b(4))),
                            Div(
                                Span("Multi-select", cls=combine_classes(badge, badge_colors.primary, m.r(2))),
                                Span("List view", cls=combine_classes(badge, badge_colors.secondary, m.r(2))),
                                Span("All files", cls=combine_classes(badge, badge_colors.accent)),
                                cls=m.b(4)
                            ),
                            A("Open Browser →",
                              href=demo_general.to(),
                              cls=combine_classes(btn, btn_colors.primary)),
                            cls=card_body
                        ),
                        cls=combine_classes(card, bg_dui.base_200)
                    ),

                    # Database picker card
                    Div(
                        Div(
                            H2("Database File Picker",
                               cls=combine_classes(font_size.xl, font_weight.semibold, m.b(2))),
                            P("Pick .db and .sqlite files for your application.",
                              cls=combine_classes(text_dui.base_content, m.b(4))),
                            Div(
                                Span("Multi-select", cls=combine_classes(badge, badge_colors.primary, m.r(2))),
                                Span("Files only", cls=combine_classes(badge, badge_colors.secondary, m.r(2))),
                                Span(".db/.sqlite", cls=combine_classes(badge, badge_colors.info)),
                                cls=m.b(4)
                            ),
                            A("Open Picker →",
                              href=demo_db_picker.to(),
                              cls=combine_classes(btn, btn_colors.secondary)),
                            cls=card_body
                        ),
                        cls=combine_classes(card, bg_dui.base_200)
                    ),

                    # Image browser card
                    Div(
                        Div(
                            H2("Image Browser",
                               cls=combine_classes(font_size.xl, font_weight.semibold, m.b(2))),
                            P("Browse images in grid view with single selection.",
                              cls=combine_classes(text_dui.base_content, m.b(4))),
                            Div(
                                Span("Single-select", cls=combine_classes(badge, badge_colors.primary, m.r(2))),
                                Span("Grid view", cls=combine_classes(badge, badge_colors.secondary, m.r(2))),
                                Span("Images only", cls=combine_classes(badge, badge_colors.success)),
                                cls=m.b(4)
                            ),
                            A("Open Gallery →",
                              href=demo_image.to(),
                              cls=combine_classes(btn, btn_colors.accent)),
                            cls=card_body
                        ),
                        cls=combine_classes(card, bg_dui.base_200)
                    ),

                    cls=combine_classes(
                        grid_display, grid_cols(1),
                        grid_cols(3).md,
                        gap(6), m.b(8)
                    )
                ),

                # Info section
                Div(
                    H2("Features", cls=combine_classes(font_size._2xl, font_weight.bold, m.b(4))),
                    Div(
                        Div("✓ Interactive directory navigation", cls=m.b(2)),
                        Div("✓ Multiple selection modes (none, single, multiple)", cls=m.b(2)),
                        Div("✓ List and grid view modes", cls=m.b(2)),
                        Div("✓ Extension-based filtering", cls=m.b(2)),
                        Div("✓ Sortable columns (name, size, date)", cls=m.b(2)),
                        Div("✓ Breadcrumb navigation", cls=m.b(2)),
                        Div("✓ Home/parent/refresh buttons", cls=m.b(2)),
                        Div("✓ HTMX-powered partial updates", cls=m.b(2)),
                        Div("✓ Extensible provider pattern", cls=m.b(2)),
                        cls=combine_classes(text_align.left, max_w.md, m.x.auto)
                    ),
                    cls=m.b(8)
                ),

                cls=combine_classes(
                    container,
                    max_w._6xl,
                    m.x.auto,
                    p(8),
                    text_align.center
                )
            )

        return handle_htmx_request(
            request,
            home_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_general(request):
        """General file browser demo."""

        def browser_content():
            state = browser_states["general"]
            listing = provider.list_directory(state.current_path)

            return Div(
                # Header
                Div(
                    H1("General File Browser",
                       cls=combine_classes(font_size._2xl, font_weight.bold)),
                    P("Multi-select enabled. Click files/folders to select, navigate directories.",
                      cls=combine_classes(text_dui.base_content, font_size.sm)),
                    cls=combine_classes(m.b(4))
                ),

                # Selection display
                Div(
                    Span("Selected: ", cls=font_weight.semibold),
                    Span(
                        ", ".join([Path(p).name for p in state.selection.selected_paths]) or "None",
                        cls=text_dui.base_content
                    ),
                    cls=combine_classes(m.b(4), p(2), bg_dui.base_200, rounded())
                ),

                # Browser
                Div(
                    render_file_browser(
                        listing=listing,
                        config=general_config,
                        state=state,
                        navigate_url=general_browser_router.navigate.to(),
                        select_url=general_browser_router.select.to(),
                        toggle_view_url=general_browser_router.toggle_view.to(),
                        change_sort_url=general_browser_router.change_sort.to(),
                        refresh_url=general_browser_router.refresh.to(),
                        path_input_url=general_browser_router.path_input.to(),
                        home_path=home_path,
                    ),
                    cls=combine_classes(h(96), border(), rounded.lg, overflow.hidden)
                ),

                # Scroll preservation for select operations
                Script(generate_scroll_preservation_script(general_config.content_id)),

                cls=combine_classes(container, max_w._5xl, m.x.auto, p(6))
            )

        return handle_htmx_request(
            request,
            browser_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_db_picker(request):
        """Database file picker demo."""

        def browser_content():
            state = browser_states["db_picker"]
            listing = provider.list_directory(state.current_path)

            return Div(
                # Header
                Div(
                    H1("Database File Picker",
                       cls=combine_classes(font_size._2xl, font_weight.bold)),
                    P("Only .db, .sqlite, and .sqlite3 files are shown. Multi-select enabled.",
                      cls=combine_classes(text_dui.base_content, font_size.sm)),
                    cls=combine_classes(m.b(4))
                ),

                # Selection display
                Div(
                    Span("Selected databases: ", cls=font_weight.semibold),
                    Span(
                        ", ".join([Path(p).name for p in state.selection.selected_paths]) or "None",
                        cls=text_dui.base_content
                    ),
                    cls=combine_classes(m.b(4), p(2), bg_dui.base_200, rounded())
                ),

                # Browser
                Div(
                    render_file_browser(
                        listing=listing,
                        config=db_picker_config,
                        state=state,
                        navigate_url=db_picker_browser_router.navigate.to(),
                        select_url=db_picker_browser_router.select.to(),
                        toggle_view_url=db_picker_browser_router.toggle_view.to(),
                        change_sort_url=db_picker_browser_router.change_sort.to(),
                        refresh_url=db_picker_browser_router.refresh.to(),
                        path_input_url=db_picker_browser_router.path_input.to(),
                        home_path=home_path,
                    ),
                    cls=combine_classes(h(96), border(), rounded.lg, overflow.hidden)
                ),

                cls=combine_classes(container, max_w._5xl, m.x.auto, p(6))
            )

        return handle_htmx_request(
            request,
            browser_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_image(request):
        """Image browser demo."""

        def browser_content():
            state = browser_states["image"]
            listing = provider.list_directory(state.current_path)

            return Div(
                # Header
                Div(
                    H1("Image Browser",
                       cls=combine_classes(font_size._2xl, font_weight.bold)),
                    P("Grid view with image file filtering. Single selection mode.",
                      cls=combine_classes(text_dui.base_content, font_size.sm)),
                    cls=combine_classes(m.b(4))
                ),

                # Selection display
                Div(
                    Span("Selected image: ", cls=font_weight.semibold),
                    Span(
                        Path(state.selection.selected_paths[0]).name if state.selection.selected_paths else "None",
                        cls=text_dui.base_content
                    ),
                    cls=combine_classes(m.b(4), p(2), bg_dui.base_200, rounded())
                ),

                # Browser
                Div(
                    render_file_browser(
                        listing=listing,
                        config=image_config,
                        state=state,
                        navigate_url=image_browser_router.navigate.to(),
                        select_url=image_browser_router.select.to(),
                        toggle_view_url=image_browser_router.toggle_view.to(),
                        change_sort_url=image_browser_router.change_sort.to(),
                        refresh_url=image_browser_router.refresh.to(),
                        path_input_url=image_browser_router.path_input.to(),
                        home_path=home_path,
                    ),
                    cls=combine_classes(h(96), border(), rounded.lg, overflow.hidden)
                ),

                cls=combine_classes(container, max_w._5xl, m.x.auto, p(6))
            )

        return handle_htmx_request(
            request,
            browser_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    # Create navbar
    navbar = create_navbar(
        title="File Browser Demo",
        nav_items=[
            ("Home", index),
            ("General", demo_general),
            ("DB Picker", demo_db_picker),
            ("Images", demo_image),
        ],
        home_route=index,
        theme_selector=True
    )

    # Register all routes
    register_routes(
        app,
        router,
        general_browser_router,
        db_picker_browser_router,
        image_browser_router,
    )

    # Debug: Print registered routes
    print("\n" + "=" * 70)
    print("Registered Routes:")
    print("=" * 70)
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")

    print("\n" + "=" * 70)
    print("Demo App Ready!")
    print("=" * 70)
    print("\n Library Components:")
    print("  - LocalFileSystemProvider - Local file system navigation")
    print("  - FileBrowserConfig - Configurable browser settings")
    print("  - BrowserState - Selection and view state tracking")
    print("  - render_file_browser - Main UI component")
    print("  - HTMX handlers - Smooth partial page updates")
    print("=" * 70 + "\n")

    return app


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    # Call main to initialize everything and get the app
    app = main()

    def open_browser(url):
        print(f"Opening browser at {url}")
        webbrowser.open(url)

    port = 5032
    host = "0.0.0.0"
    display_host = 'localhost' if host in ['0.0.0.0', '127.0.0.1'] else host

    print(f"Server: http://{display_host}:{port}")
    print("\nAvailable routes:")
    print(f"  http://{display_host}:{port}/              - Homepage with demo overview")
    print(f"  http://{display_host}:{port}/demo_general  - General file browser")
    print(f"  http://{display_host}:{port}/demo_db_picker - Database file picker")
    print(f"  http://{display_host}:{port}/demo_image    - Image browser (grid view)")
    print("\n" + "=" * 70 + "\n")

    # Open browser after a short delay
    timer = threading.Timer(1.5, lambda: open_browser(f"http://localhost:{port}"))
    timer.daemon = True
    timer.start()

    # Start server
    uvicorn.run(app, host=host, port=port)
