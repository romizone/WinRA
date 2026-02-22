"""WinRA - macOS Native Style Archive Manager."""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import darkdetect

from app.archive_ops import (
    extract_zip,
    extract_rar,
    compress_to_zip,
    convert_rar_to_zip,
    convert_zip_to_rar,
    get_archive_info,
    format_size,
)
from app.utils import (
    is_supported_archive,
    get_archive_type,
    get_default_extract_dir,
    get_default_output_path,
    ensure_dir,
)


# ── macOS Color System ──────────────────────────────────────────────
class MacColors:
    """macOS-style color palette with light/dark mode support."""

    # System accent colors
    BLUE = "#007AFF"
    BLUE_HOVER = "#0062CC"
    PURPLE = "#AF52DE"
    PINK = "#FF2D55"
    RED = "#FF3B30"
    ORANGE = "#FF9500"
    YELLOW = "#FFCC00"
    GREEN = "#34C759"
    TEAL = "#5AC8FA"
    INDIGO = "#5856D6"

    # Gradient pair for accent
    GRAD_START = "#6C5CE7"
    GRAD_END = "#0984E3"

    class Light:
        BG = "#F5F5F7"
        BG_SECONDARY = "#FFFFFF"
        BG_TERTIARY = "#F0F0F2"
        SIDEBAR_BG = "#F0F0F2"
        SIDEBAR_HOVER = "#E5E5EA"
        SIDEBAR_ACTIVE = "#D1D1D6"
        TEXT_PRIMARY = "#1D1D1F"
        TEXT_SECONDARY = "#6E6E73"
        TEXT_TERTIARY = "#AEAEB2"
        SEPARATOR = "#D1D1D6"
        CARD_BG = "#FFFFFF"
        CARD_BORDER = "#E5E5EA"
        TOOLBAR_BG = "#F8F8FA"
        INPUT_BG = "#FFFFFF"
        INPUT_BORDER = "#D1D1D6"
        TAG_BG = "#E8E8ED"
        HIGHLIGHT = "#E3F0FF"

    class Dark:
        BG = "#1D1D1F"
        BG_SECONDARY = "#2C2C2E"
        BG_TERTIARY = "#3A3A3C"
        SIDEBAR_BG = "#252528"
        SIDEBAR_HOVER = "#3A3A3C"
        SIDEBAR_ACTIVE = "#48484A"
        TEXT_PRIMARY = "#F5F5F7"
        TEXT_SECONDARY = "#A1A1A6"
        TEXT_TERTIARY = "#636366"
        SEPARATOR = "#3A3A3C"
        CARD_BG = "#2C2C2E"
        CARD_BORDER = "#3A3A3C"
        TOOLBAR_BG = "#2C2C2E"
        INPUT_BG = "#3A3A3C"
        INPUT_BORDER = "#48484A"
        TAG_BG = "#3A3A3C"
        HIGHLIGHT = "#1C3A5E"


class WinRAApp(ctk.CTk):
    """Main application window - macOS native style."""

    def __init__(self):
        super().__init__()

        # Detect system appearance
        self._dark_mode = darkdetect.isDark()
        mode = "dark" if self._dark_mode else "light"
        ctk.set_appearance_mode(mode)
        self.C = MacColors.Dark if self._dark_mode else MacColors.Light

        self.title("WinRA")
        self.geometry("1060x680")
        self.minsize(900, 580)

        self._current_tab = "extract"
        self._selected_files: list[str] = []
        self._is_processing = False
        self._archive_contents: list[dict] = []
        self._reset_timer = None

        self.configure(fg_color=self.C.BG)
        self._setup_styles()
        self._build_ui()
        self._switch_tab("extract")

    def _setup_styles(self):
        """Configure ttk styles for native macOS look."""
        style = ttk.Style()
        style.theme_use("default")

        # Treeview
        style.configure("Mac.Treeview",
                         background=self.C.BG_SECONDARY,
                         foreground=self.C.TEXT_PRIMARY,
                         fieldbackground=self.C.BG_SECONDARY,
                         font=("SF Pro Text", 12),
                         rowheight=30,
                         borderwidth=0,
                         relief="flat")
        style.configure("Mac.Treeview.Heading",
                         background=self.C.TOOLBAR_BG,
                         foreground=self.C.TEXT_SECONDARY,
                         font=("SF Pro Text", 11, "bold"),
                         relief="flat",
                         borderwidth=0)
        style.map("Mac.Treeview",
                   background=[("selected", MacColors.BLUE)],
                   foreground=[("selected", "#FFFFFF")])
        style.map("Mac.Treeview.Heading",
                   background=[("active", self.C.SIDEBAR_HOVER)])

        # Scrollbar
        style.configure("Mac.Vertical.TScrollbar",
                         gripcount=0,
                         background=self.C.BG_SECONDARY,
                         troughcolor=self.C.BG_SECONDARY,
                         borderwidth=0,
                         relief="flat")

    # ─── UI Construction ─────────────────────────────────────────────

    def _build_ui(self):
        """Build the macOS-style UI with sidebar layout."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_content()

    def _build_sidebar(self):
        """Build macOS-style sidebar with navigation."""
        self._sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0,
            fg_color=self.C.SIDEBAR_BG,
            border_width=0,
        )
        sidebar = self._sidebar
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)

        # ── App branding ──
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 6))

        # Gradient-ish accent circle
        icon_frame = ctk.CTkFrame(
            brand_frame, width=40, height=40,
            corner_radius=10,
            fg_color=MacColors.BLUE,
        )
        icon_frame.pack(side="left", padx=(0, 10))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame, text="W",
            font=ctk.CTkFont(family="SF Pro Display", size=20, weight="bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x")

        ctk.CTkLabel(
            title_frame, text="WinRA",
            font=ctk.CTkFont(family="SF Pro Display", size=17, weight="bold"),
            text_color=self.C.TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text="Archive Manager",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.C.TEXT_SECONDARY,
        ).pack(anchor="w")

        # ── Separator ──
        ctk.CTkFrame(
            sidebar, height=1, fg_color=self.C.SEPARATOR, corner_radius=0,
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 12))

        # ── Section label ──
        ctk.CTkLabel(
            sidebar, text="TOOLS",
            font=ctk.CTkFont(family="SF Pro Text", size=10, weight="bold"),
            text_color=self.C.TEXT_TERTIARY,
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(0, 6))

        # ── Navigation buttons ──
        nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew", padx=10)
        nav_frame.grid_columnconfigure(0, weight=1)

        self._nav_buttons = {}
        nav_items = [
            ("extract", "Extract Archive", "\U0001F4E6"),
            ("compress", "Compress Files", "\U0001F5DC\uFE0F"),
            ("convert", "Convert Format", "\U0001F504"),
        ]

        for i, (key, label, icon) in enumerate(nav_items):
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}   {label}",
                height=36,
                font=ctk.CTkFont(family="SF Pro Text", size=13),
                fg_color="transparent",
                hover_color=self.C.SIDEBAR_HOVER,
                text_color=self.C.TEXT_PRIMARY,
                anchor="w",
                corner_radius=8,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.grid(row=i, column=0, sticky="ew", pady=1)
            self._nav_buttons[key] = btn

        # ── Bottom area ──
        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.grid(row=5, column=0, sticky="sew", padx=10, pady=(0, 16))
        bottom_frame.grid_columnconfigure(0, weight=1)

        # Theme toggle
        theme_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            theme_frame,
            text="\u2600\uFE0F" if self._dark_mode else "\U0001F319",
            font=ctk.CTkFont(size=14),
            text_color=self.C.TEXT_SECONDARY,
        ).pack(side="left", padx=(10, 6))

        self._theme_label = ctk.CTkLabel(
            theme_frame, text="Dark Mode" if self._dark_mode else "Light Mode",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.C.TEXT_SECONDARY,
        )
        self._theme_label.pack(side="left")

        self._theme_switch = ctk.CTkSwitch(
            theme_frame, text="", width=42,
            progress_color=MacColors.BLUE,
            command=self._toggle_theme,
        )
        if self._dark_mode:
            self._theme_switch.select()
        self._theme_switch.pack(side="right", padx=(0, 6))

        # Version
        ctk.CTkLabel(
            bottom_frame, text="v1.0 for macOS",
            font=ctk.CTkFont(family="SF Pro Text", size=10),
            text_color=self.C.TEXT_TERTIARY,
        ).pack(anchor="center")

    def _build_main_content(self):
        """Build the main content area."""
        self._main = ctk.CTkFrame(self, corner_radius=0, fg_color=self.C.BG)
        main = self._main
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # ── Toolbar ──
        self._toolbar = ctk.CTkFrame(
            main, height=50, corner_radius=0,
            fg_color=self.C.TOOLBAR_BG,
            border_width=0,
        )
        self._toolbar.grid(row=0, column=0, sticky="ew")
        self._toolbar.grid_propagate(False)
        self._toolbar.grid_columnconfigure(2, weight=1)

        # Mode title
        self._mode_title = ctk.CTkLabel(
            self._toolbar, text="Extract Archive",
            font=ctk.CTkFont(family="SF Pro Display", size=16, weight="bold"),
            text_color=self.C.TEXT_PRIMARY,
        )
        self._mode_title.grid(row=0, column=0, padx=(20, 16), pady=12, sticky="w")

        # Toolbar separator
        ctk.CTkFrame(
            self._toolbar, width=1, fg_color=self.C.SEPARATOR,
        ).grid(row=0, column=1, sticky="ns", pady=10)

        # Toolbar actions frame
        self._toolbar_actions = ctk.CTkFrame(self._toolbar, fg_color="transparent")
        self._toolbar_actions.grid(row=0, column=2, sticky="ew", padx=12)

        # ── Separator under toolbar ──
        ctk.CTkFrame(
            main, height=1, fg_color=self.C.SEPARATOR, corner_radius=0,
        ).grid(row=1, column=0, sticky="ew")

        # ── Content Area ──
        self._content = ctk.CTkFrame(main, corner_radius=0, fg_color=self.C.BG)
        content = self._content
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        # ── Drop Zone / Action Card ──
        self._top_card = ctk.CTkFrame(
            content, height=120,
            fg_color=self.C.CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=self.C.CARD_BORDER,
        )
        self._top_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._top_card.grid_propagate(False)
        self._top_card.grid_columnconfigure(1, weight=1)
        self._top_card.grid_rowconfigure(0, weight=1)

        # Drop zone (left side of card)
        self._drop_zone = ctk.CTkFrame(
            self._top_card, width=160,
            fg_color=self.C.HIGHLIGHT,
            corner_radius=12,
            border_width=2,
            border_color=MacColors.BLUE,
        )
        self._drop_zone.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self._drop_zone.grid_propagate(False)
        self._drop_zone.grid_columnconfigure(0, weight=1)
        self._drop_zone.grid_rowconfigure(0, weight=1)

        self._drop_icon = ctk.CTkLabel(
            self._drop_zone, text="\U0001F4C2",
            font=ctk.CTkFont(size=28),
        )
        self._drop_icon.grid(row=0, column=0, pady=(12, 0))

        self._drop_text = ctk.CTkLabel(
            self._drop_zone, text="Click to open",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=MacColors.BLUE,
        )
        self._drop_text.grid(row=1, column=0, pady=(0, 12))

        self._drop_zone.bind("<Button-1>", lambda e: self._browse_files())
        self._drop_icon.bind("<Button-1>", lambda e: self._browse_files())
        self._drop_text.bind("<Button-1>", lambda e: self._browse_files())

        # File info (right side of card)
        info_area = ctk.CTkFrame(self._top_card, fg_color="transparent")
        info_area.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        info_area.grid_columnconfigure(0, weight=1)

        self._file_title = ctk.CTkLabel(
            info_area, text="No file selected",
            font=ctk.CTkFont(family="SF Pro Display", size=14, weight="bold"),
            text_color=self.C.TEXT_PRIMARY,
            anchor="w",
        )
        self._file_title.grid(row=0, column=0, sticky="w", pady=(4, 2))

        self._file_subtitle = ctk.CTkLabel(
            info_area, text="Open an archive or add files to get started",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.C.TEXT_SECONDARY,
            anchor="w",
            wraplength=400,
        )
        self._file_subtitle.grid(row=1, column=0, sticky="w")

        # Tags row
        self._tags_frame = ctk.CTkFrame(info_area, fg_color="transparent")
        self._tags_frame.grid(row=2, column=0, sticky="w", pady=(6, 0))

        # Action buttons in card
        btn_frame = ctk.CTkFrame(self._top_card, fg_color="transparent", width=180)
        btn_frame.grid(row=0, column=2, sticky="nse", padx=12, pady=16)

        self._action_btn = ctk.CTkButton(
            btn_frame,
            text="Extract",
            height=38,
            width=150,
            font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
            fg_color=MacColors.BLUE,
            hover_color=MacColors.BLUE_HOVER,
            text_color="#FFFFFF",
            corner_radius=10,
            command=self._execute_action,
        )
        self._action_btn.pack(pady=(0, 6))

        self._secondary_btn = ctk.CTkButton(
            btn_frame,
            text="Browse output...",
            height=32,
            width=150,
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            fg_color="transparent",
            hover_color=self.C.SIDEBAR_HOVER,
            text_color=MacColors.BLUE,
            border_width=1,
            border_color=MacColors.BLUE,
            corner_radius=8,
            command=self._browse_output,
        )
        self._secondary_btn.pack()

        # ── Output path bar ──
        self._output_bar = ctk.CTkFrame(
            content, height=38,
            fg_color=self.C.CARD_BG,
            corner_radius=10,
            border_width=1,
            border_color=self.C.CARD_BORDER,
        )
        output_bar = self._output_bar
        output_bar.grid(row=1, column=0, sticky="new", pady=(0, 10))
        output_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            output_bar, text="Output:",
            font=ctk.CTkFont(family="SF Pro Text", size=11, weight="bold"),
            text_color=self.C.TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(12, 6), pady=6)

        self._output_entry = ctk.CTkEntry(
            output_bar,
            font=ctk.CTkFont(family="SF Mono", size=11),
            height=26,
            fg_color="transparent",
            border_width=0,
            text_color=self.C.TEXT_PRIMARY,
            placeholder_text="Select output location...",
            placeholder_text_color=self.C.TEXT_TERTIARY,
        )
        self._output_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=6)

        self._output_finder_btn = ctk.CTkButton(
            output_bar, text="Show in Finder",
            width=100, height=24,
            font=ctk.CTkFont(family="SF Pro Text", size=10),
            fg_color=self.C.TAG_BG,
            hover_color=self.C.SIDEBAR_HOVER,
            text_color=self.C.TEXT_SECONDARY,
            corner_radius=6,
            command=self._open_in_finder,
        )
        self._output_finder_btn.grid(row=0, column=2, padx=(4, 8), pady=6)

        # ── Treeview / File list card ──
        self._tree_card = ctk.CTkFrame(
            content,
            fg_color=self.C.CARD_BG,
            corner_radius=14,
            border_width=1,
            border_color=self.C.CARD_BORDER,
        )
        tree_card = self._tree_card
        tree_card.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        tree_card.grid_columnconfigure(0, weight=1)
        tree_card.grid_rowconfigure(1, weight=1)

        # Tree header
        tree_header = ctk.CTkFrame(tree_card, height=36, fg_color="transparent",
                                    corner_radius=0)
        tree_header.grid(row=0, column=0, sticky="ew")
        tree_header.grid_columnconfigure(1, weight=1)

        self._tree_title = ctk.CTkLabel(
            tree_header, text="Contents",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=self.C.TEXT_PRIMARY,
        )
        self._tree_title.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self._tree_count = ctk.CTkLabel(
            tree_header, text="",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.C.TEXT_TERTIARY,
        )
        self._tree_count.grid(row=0, column=1, padx=16, pady=8, sticky="e")

        # Separator
        ctk.CTkFrame(
            tree_card, height=1, fg_color=self.C.CARD_BORDER, corner_radius=0,
        ).grid(row=0, column=0, sticky="sew", padx=1)

        # Treeview
        self._tree_frame = ctk.CTkFrame(tree_card, fg_color=self.C.CARD_BG, corner_radius=0)
        tree_frame = self._tree_frame
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=1, pady=(0, 1))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("size", "compressed", "type"),
            show="tree headings",
            style="Mac.Treeview",
        )
        self._tree.heading("#0", text="  Name", anchor="w")
        self._tree.heading("size", text="Size", anchor="e")
        self._tree.heading("compressed", text="Packed", anchor="e")
        self._tree.heading("type", text="Kind", anchor="w")

        self._tree.column("#0", width=320, minwidth=200)
        self._tree.column("size", width=90, minwidth=70, anchor="e")
        self._tree.column("compressed", width=90, minwidth=70, anchor="e")
        self._tree.column("type", width=70, minwidth=50)

        tree_vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self._tree.yview, style="Mac.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=tree_vsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        tree_vsb.grid(row=0, column=1, sticky="ns")

        # Empty state
        self._empty_state = ctk.CTkFrame(tree_frame, fg_color=self.C.CARD_BG)
        self._empty_state.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self._empty_state, text="\U0001F4C1",
            font=ctk.CTkFont(size=40),
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            self._empty_state, text="No files to display",
            font=ctk.CTkFont(family="SF Pro Display", size=15, weight="bold"),
            text_color=self.C.TEXT_PRIMARY,
        ).pack()

        self._empty_subtitle = ctk.CTkLabel(
            self._empty_state,
            text="Open an archive to view contents, or\nadd files to create a new archive.",
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=self.C.TEXT_SECONDARY,
            justify="center",
        )
        self._empty_subtitle.pack(pady=(4, 0))

        # ── Progress bar (bottom of content) ──
        self._progress_frame = ctk.CTkFrame(content, fg_color="transparent", height=30)
        self._progress_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        self._progress_frame.grid_columnconfigure(1, weight=1)

        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="Ready",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.C.TEXT_TERTIARY,
        )
        self._progress_label.grid(row=0, column=0, padx=(0, 10))

        self._progress = ctk.CTkProgressBar(
            self._progress_frame,
            height=6,
            progress_color=MacColors.BLUE,
            fg_color=self.C.SEPARATOR,
            corner_radius=3,
        )
        self._progress.grid(row=0, column=1, sticky="ew")
        self._progress.set(0)

    # ─── Tags / Badges ───────────────────────────────────────────────

    def _clear_tags(self):
        """Remove all tags from tags frame."""
        for w in self._tags_frame.winfo_children():
            w.destroy()

    def _add_tag(self, text: str, color: str = None):
        """Add a small tag/badge to the file info area."""
        if color is None:
            color = MacColors.BLUE
        tag = ctk.CTkFrame(
            self._tags_frame,
            fg_color=color,
            corner_radius=6,
            height=22,
        )
        tag.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            tag, text=text,
            font=ctk.CTkFont(family="SF Pro Text", size=10, weight="bold"),
            text_color="#FFFFFF",
        ).pack(padx=8, pady=2)

    # ─── Tab Switching ───────────────────────────────────────────────

    def _switch_tab(self, tab: str):
        """Switch navigation tab."""
        self._current_tab = tab
        self._selected_files.clear()
        self._archive_contents.clear()

        # Update sidebar button styling
        for key, btn in self._nav_buttons.items():
            if key == tab:
                btn.configure(
                    fg_color=MacColors.BLUE,
                    text_color="#FFFFFF",
                    hover_color=MacColors.BLUE_HOVER,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.C.TEXT_PRIMARY,
                    hover_color=self.C.SIDEBAR_HOVER,
                )

        self._reset_ui()

        if tab == "extract":
            self._mode_title.configure(text="Extract Archive")
            self._action_btn.configure(text="Extract", fg_color=MacColors.BLUE,
                                        hover_color=MacColors.BLUE_HOVER)
            self._drop_text.configure(text="Open archive file")
            self._empty_subtitle.configure(
                text="Open a ZIP or RAR archive\nto view and extract its contents."
            )
            self._tree_title.configure(text="Archive Contents")
            self._build_toolbar_extract()

        elif tab == "compress":
            self._mode_title.configure(text="Compress Files")
            self._action_btn.configure(text="Create ZIP", fg_color=MacColors.GREEN,
                                        hover_color="#2EA54D")
            self._drop_text.configure(text="Add files or folders")
            self._empty_subtitle.configure(
                text="Select files or folders\nto compress into a ZIP archive."
            )
            self._tree_title.configure(text="Files to Compress")
            self._build_toolbar_compress()

        elif tab == "convert":
            self._mode_title.configure(text="Convert Format")
            self._action_btn.configure(text="Convert", fg_color=MacColors.PURPLE,
                                        hover_color="#9B3DC4")
            self._drop_text.configure(text="Open archive to convert")
            self._empty_subtitle.configure(
                text="Open a RAR or ZIP archive\nto convert it to another format."
            )
            self._tree_title.configure(text="Archive Contents")
            self._build_toolbar_convert()

    def _reset_ui(self):
        """Reset UI state."""
        self._clear_tree()
        self._output_entry.delete(0, "end")
        self._progress.set(0)
        self._progress_label.configure(text="Ready")
        self._file_title.configure(text="No file selected")
        self._file_subtitle.configure(text="Open an archive or add files to get started")
        self._tree_count.configure(text="")
        self._clear_tags()
        self._empty_state.place(relx=0.5, rely=0.5, anchor="center")
        self._drop_icon.configure(text="\U0001F4C2")

    def _clear_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

    # ─── Toolbar builders ────────────────────────────────────────────

    def _clear_toolbar(self):
        for w in self._toolbar_actions.winfo_children():
            w.destroy()

    def _toolbar_btn(self, parent, text, command, icon=""):
        """Create a macOS-style toolbar button."""
        display = f"{icon}  {text}" if icon else text
        return ctk.CTkButton(
            parent, text=display,
            height=30, width=0,
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            fg_color="transparent",
            hover_color=self.C.SIDEBAR_HOVER,
            text_color=self.C.TEXT_PRIMARY,
            corner_radius=6,
            command=command,
        )

    def _build_toolbar_extract(self):
        self._clear_toolbar()
        b1 = self._toolbar_btn(self._toolbar_actions, "Open", self._browse_files, "\U0001F4C2")
        b1.pack(side="left", padx=2)
        b2 = self._toolbar_btn(self._toolbar_actions, "Extract Here", self._extract_here, "\U0001F4E5")
        b2.pack(side="left", padx=2)
        b3 = self._toolbar_btn(self._toolbar_actions, "Info", self._show_archive_info, "\u2139\uFE0F")
        b3.pack(side="left", padx=2)

    def _build_toolbar_compress(self):
        self._clear_toolbar()
        b1 = self._toolbar_btn(self._toolbar_actions, "Add Files", self._browse_files, "\u2795")
        b1.pack(side="left", padx=2)
        b2 = self._toolbar_btn(self._toolbar_actions, "Add Folder", self._browse_folder, "\U0001F4C1")
        b2.pack(side="left", padx=2)
        b3 = self._toolbar_btn(self._toolbar_actions, "Clear", self._clear_selection, "\u274C")
        b3.pack(side="left", padx=2)

    def _build_toolbar_convert(self):
        self._clear_toolbar()
        b1 = self._toolbar_btn(self._toolbar_actions, "Open Archive", self._browse_files, "\U0001F4C2")
        b1.pack(side="left", padx=2)
        b2 = self._toolbar_btn(self._toolbar_actions, "RAR \u2192 ZIP", lambda: self._do_convert("rar_to_zip"), "\U0001F504")
        b2.pack(side="left", padx=2)
        b3 = self._toolbar_btn(self._toolbar_actions, "ZIP \u2192 RAR", lambda: self._do_convert("zip_to_rar"), "\U0001F504")
        b3.pack(side="left", padx=2)

    # ─── Theme ───────────────────────────────────────────────────────

    def _toggle_theme(self):
        """Toggle dark/light mode."""
        self._dark_mode = not self._dark_mode
        mode = "dark" if self._dark_mode else "light"
        ctk.set_appearance_mode(mode)
        self.C = MacColors.Dark if self._dark_mode else MacColors.Light

        # Update colors that need manual refresh
        self.configure(fg_color=self.C.BG)
        self._theme_label.configure(text="Dark Mode" if self._dark_mode else "Light Mode")

        # Sidebar
        self._sidebar.configure(fg_color=self.C.SIDEBAR_BG)

        # Nav buttons (non-active ones)
        for key, btn in self._nav_buttons.items():
            if key == self._current_tab:
                btn.configure(hover_color=MacColors.BLUE_HOVER)
            else:
                btn.configure(
                    text_color=self.C.TEXT_PRIMARY,
                    hover_color=self.C.SIDEBAR_HOVER,
                )

        # Main area
        self._main.configure(fg_color=self.C.BG)
        self._content.configure(fg_color=self.C.BG)
        self._toolbar.configure(fg_color=self.C.TOOLBAR_BG)
        self._mode_title.configure(text_color=self.C.TEXT_PRIMARY)

        # Cards
        self._top_card.configure(fg_color=self.C.CARD_BG, border_color=self.C.CARD_BORDER)
        self._drop_zone.configure(
            fg_color=self.C.HIGHLIGHT,
        )

        # File info
        self._file_title.configure(text_color=self.C.TEXT_PRIMARY)
        self._file_subtitle.configure(text_color=self.C.TEXT_SECONDARY)

        # Output bar
        self._output_bar.configure(fg_color=self.C.CARD_BG, border_color=self.C.CARD_BORDER)
        self._output_entry.configure(text_color=self.C.TEXT_PRIMARY)
        self._output_finder_btn.configure(
            fg_color=self.C.TAG_BG, hover_color=self.C.SIDEBAR_HOVER,
            text_color=self.C.TEXT_SECONDARY,
        )
        self._secondary_btn.configure(hover_color=self.C.SIDEBAR_HOVER)

        # Tree card
        self._tree_card.configure(fg_color=self.C.CARD_BG, border_color=self.C.CARD_BORDER)
        self._tree_frame.configure(fg_color=self.C.CARD_BG)
        self._tree_title.configure(text_color=self.C.TEXT_PRIMARY)
        self._tree_count.configure(text_color=self.C.TEXT_TERTIARY)
        self._empty_state.configure(fg_color=self.C.CARD_BG)
        self._empty_subtitle.configure(text_color=self.C.TEXT_SECONDARY)

        # Progress
        self._progress_label.configure(text_color=self.C.TEXT_TERTIARY)
        self._progress.configure(fg_color=self.C.SEPARATOR)

        # Treeview ttk styles
        self._setup_styles()

    # ─── File Browsing ───────────────────────────────────────────────

    def _browse_files(self):
        if self._is_processing:
            return

        if self._current_tab == "extract":
            filetypes = [("Archive files", "*.zip *.rar"), ("ZIP", "*.zip"),
                          ("RAR", "*.rar"), ("All", "*.*")]
            path = filedialog.askopenfilename(title="Open Archive", filetypes=filetypes)
            if path:
                self._selected_files = [path]
                self._on_archive_selected(path)

        elif self._current_tab == "compress":
            paths = filedialog.askopenfilenames(title="Select Files")
            if paths:
                # Deduplicate: only add files not already selected
                existing = set(self._selected_files)
                for p in paths:
                    if p not in existing:
                        self._selected_files.append(p)
                        existing.add(p)
                self._on_compress_files_selected()

        elif self._current_tab == "convert":
            filetypes = [("Archive files", "*.zip *.rar"), ("RAR", "*.rar"),
                          ("ZIP", "*.zip"), ("All", "*.*")]
            path = filedialog.askopenfilename(title="Open Archive", filetypes=filetypes)
            if path:
                self._selected_files = [path]
                self._on_archive_selected(path)

    def _browse_folder(self):
        if self._is_processing:
            return
        folder = filedialog.askdirectory(title="Select Folder")
        if folder and folder not in self._selected_files:
            self._selected_files.append(folder)
            self._on_compress_files_selected()

    def _browse_output(self):
        if self._current_tab == "extract":
            path = filedialog.askdirectory(title="Extract To")
        elif self._current_tab == "compress":
            path = filedialog.asksaveasfilename(title="Save ZIP As", defaultextension=".zip",
                                                  filetypes=[("ZIP", "*.zip")])
        elif self._current_tab == "convert":
            src = self._selected_files[0] if self._selected_files else ""
            src_ext = os.path.splitext(src)[1].lower()
            target = ".zip" if src_ext == ".rar" else ".rar"
            path = filedialog.asksaveasfilename(title="Save As", defaultextension=target,
                                                  filetypes=[(f"{target.upper()}", f"*{target}")])
        else:
            return
        if path:
            self._output_entry.delete(0, "end")
            self._output_entry.insert(0, path)

    # ─── Selection Handlers ──────────────────────────────────────────

    def _on_archive_selected(self, path: str):
        name = os.path.basename(path)
        info = get_archive_info(path)
        self._archive_contents = info.get("files", [])

        # Update drop zone
        ext = os.path.splitext(path)[1].lower()
        self._drop_icon.configure(text="\U0001F4E6")
        display_name = name if len(name) <= 20 else name[:17] + "..."
        self._drop_text.configure(text=display_name)

        # Update file info
        self._file_title.configure(text=name)
        ratio = ""
        if info["total_size"] > 0 and info["size"] > 0:
            r = max(0, (1 - info["size"] / info["total_size"]) * 100)
            ratio = f"  |  {r:.0f}% compression"
        self._file_subtitle.configure(
            text=f"{format_size(info['size'])} archive  |  {info['total_files']} files  |  "
                 f"{format_size(info['total_size'])} original{ratio}"
        )

        # Tags
        self._clear_tags()
        self._add_tag(ext.lstrip(".").upper(), MacColors.BLUE)
        self._add_tag(f"{info['total_files']} files", MacColors.INDIGO)

        # Populate tree
        self._populate_tree(info.get("files", []))
        self._tree_count.configure(text=f"{info['total_files']} items")

        # Default output
        if self._current_tab == "extract":
            default_out = get_default_extract_dir(path)
        elif self._current_tab == "convert":
            target_ext = ".zip" if ext == ".rar" else ".rar"
            default_out = get_default_output_path(path, target_ext)
        else:
            default_out = ""
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, default_out)

    def _on_compress_files_selected(self):
        total_size = 0
        total_files = 0
        tree_items = []

        for p in self._selected_files:
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        sz = os.path.getsize(fp)
                        total_size += sz
                        total_files += 1
                        tree_items.append({"name": os.path.relpath(fp, os.path.dirname(p)),
                                            "size": sz, "compressed": 0, "is_dir": False})
            else:
                sz = os.path.getsize(p)
                total_size += sz
                total_files += 1
                tree_items.append({"name": os.path.basename(p), "size": sz,
                                    "compressed": 0, "is_dir": False})

        self._populate_tree(tree_items, show_compressed=False)
        self._tree_count.configure(text=f"{total_files} items")

        self._file_title.configure(text=f"{total_files} files selected")
        self._file_subtitle.configure(text=f"Total size: {format_size(total_size)}")
        self._drop_icon.configure(text="\U0001F4C1")
        self._drop_text.configure(text=f"{total_files} files")

        self._clear_tags()
        self._add_tag(f"{total_files} files", MacColors.GREEN)
        self._add_tag(format_size(total_size), MacColors.INDIGO)

        # Default output
        if len(self._selected_files) == 1:
            base = self._selected_files[0]
        else:
            base = os.path.dirname(self._selected_files[0])
        default_out = os.path.join(os.path.dirname(base), f"{os.path.basename(base)}.zip")
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, default_out)

    def _populate_tree(self, files: list[dict], show_compressed: bool = True):
        self._clear_tree()
        if not files:
            self._empty_state.place(relx=0.5, rely=0.5, anchor="center")
            return
        self._empty_state.place_forget()

        icon_map = {
            ".txt": "\U0001F4C4", ".md": "\U0001F4C4", ".pdf": "\U0001F4D5",
            ".jpg": "\U0001F5BC", ".jpeg": "\U0001F5BC", ".png": "\U0001F5BC",
            ".gif": "\U0001F5BC", ".svg": "\U0001F5BC", ".webp": "\U0001F5BC",
            ".mp3": "\U0001F3B5", ".wav": "\U0001F3B5", ".aac": "\U0001F3B5",
            ".mp4": "\U0001F3AC", ".mov": "\U0001F3AC", ".avi": "\U0001F3AC",
            ".py": "\U0001F40D", ".js": "\U0001F7E1", ".ts": "\U0001F535",
            ".html": "\U0001F310", ".css": "\U0001F3A8", ".json": "\U0001F4CB",
            ".zip": "\U0001F4E6", ".rar": "\U0001F4E6", ".gz": "\U0001F4E6",
            ".dmg": "\U0001F4BF", ".app": "\U0001F4E6", ".exe": "\U00002699\uFE0F",
        }

        for f in files:
            if f.get("is_dir"):
                continue
            name = f.get("name", "")
            size = format_size(f.get("size", 0))
            compressed = format_size(f.get("compressed", 0)) if show_compressed and f.get("compressed") else "\u2014"
            ext = os.path.splitext(name)[1].lower() if "." in name else ""
            icon = icon_map.get(ext, "\U0001F4C4")
            kind = ext.lstrip(".").upper() or "File"

            self._tree.insert("", "end", text=f"  {icon}  {name}",
                               values=(size, compressed, kind))

    # ─── Actions ─────────────────────────────────────────────────────

    def _extract_here(self):
        if not self._selected_files:
            messagebox.showwarning("WinRA", "Open an archive first.")
            return
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, os.path.dirname(self._selected_files[0]))
        self._execute_action()

    def _do_convert(self, direction: str):
        if not self._selected_files:
            messagebox.showwarning("WinRA", "Open an archive first.")
            return
        src = self._selected_files[0]
        src_ext = os.path.splitext(src)[1].lower()
        if direction == "rar_to_zip" and src_ext != ".rar":
            messagebox.showwarning("WinRA", "Please open a RAR file for RAR \u2192 ZIP conversion.")
            return
        if direction == "zip_to_rar" and src_ext != ".zip":
            messagebox.showwarning("WinRA", "Please open a ZIP file for ZIP \u2192 RAR conversion.")
            return
        target_ext = "zip" if direction == "rar_to_zip" else "rar"
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, get_default_output_path(src, target_ext))
        self._execute_action()

    def _clear_selection(self):
        self._selected_files.clear()
        self._archive_contents.clear()
        self._reset_ui()

    def _show_archive_info(self):
        if not self._selected_files:
            messagebox.showinfo("WinRA", "No archive opened.")
            return
        info = get_archive_info(self._selected_files[0])
        msg = (
            f"File: {info['name']}\n"
            f"Path: {info['path']}\n"
            f"Archive size: {format_size(info['size'])}\n"
            f"Type: {info['type'].upper()}\n"
            f"Files: {info['total_files']}\n"
            f"Original size: {format_size(info['total_size'])}"
        )
        if info["total_size"] > 0 and info["size"] > 0:
            msg += f"\nCompression: {(1 - info['size'] / info['total_size']) * 100:.1f}%"
        messagebox.showinfo("Archive Info", msg)

    def _open_in_finder(self):
        output = self._output_entry.get().strip()
        if not output:
            return
        target = output if os.path.isdir(output) else os.path.dirname(output)
        if os.path.isdir(target):
            subprocess.run(["open", target])

    # ─── Execute ─────────────────────────────────────────────────────

    def _execute_action(self):
        if self._is_processing:
            return
        if not self._selected_files:
            messagebox.showwarning("WinRA", "Please select files first.")
            return
        output = self._output_entry.get().strip()
        if not output:
            messagebox.showwarning("WinRA", "Please set an output location.")
            return

        self._is_processing = True
        self._action_btn.configure(state="disabled")
        self._progress.set(0)
        self._progress_label.configure(text="Processing...", text_color=MacColors.BLUE)

        thread = threading.Thread(
            target=self._run_operation,
            args=(self._current_tab, list(self._selected_files), output),
            daemon=True,
        )
        thread.start()

    def _run_operation(self, mode, files, output):
        try:
            if mode == "extract":
                src = files[0]
                ensure_dir(output)
                ext = os.path.splitext(src)[1].lower()
                if ext == ".zip":
                    result = extract_zip(src, output, self._update_progress)
                elif ext == ".rar":
                    result = extract_rar(src, output, self._update_progress)
                else:
                    raise ValueError(f"Unsupported: {ext}")
                self.after(0, lambda: self._on_complete(
                    f"Extracted {len(result)} files to:\n{output}"))

            elif mode == "compress":
                result = compress_to_zip(files, output, self._update_progress)
                sz = format_size(os.path.getsize(result))
                self.after(0, lambda: self._on_complete(f"Created archive:\n{result}\n({sz})"))

            elif mode == "convert":
                src = files[0]
                ext = os.path.splitext(src)[1].lower()
                if ext == ".rar":
                    result = convert_rar_to_zip(src, output, self._update_progress)
                elif ext == ".zip":
                    result = convert_zip_to_rar(src, output, self._update_progress)
                else:
                    raise ValueError(f"Cannot convert: {ext}")
                sz = format_size(os.path.getsize(result))
                self.after(0, lambda: self._on_complete(f"Converted to:\n{result}\n({sz})"))

        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self._on_error(err_msg))

    def _update_progress(self, current, total, filename):
        pct = current / total if total > 0 else 0
        self.after(0, lambda: self._progress.set(pct))
        self.after(0, lambda: self._progress_label.configure(
            text=f"{os.path.basename(filename)}  ({current}/{total})"))

    def _on_complete(self, message):
        self._is_processing = False
        self._progress.set(1.0)
        self._progress.configure(progress_color=MacColors.GREEN)
        self._progress_label.configure(text="Done!", text_color=MacColors.GREEN)

        labels = {"extract": "Extract", "compress": "Create ZIP", "convert": "Convert"}
        colors = {"extract": MacColors.BLUE, "compress": MacColors.GREEN, "convert": MacColors.PURPLE}
        self._action_btn.configure(state="normal", text=labels.get(self._current_tab, "Go"),
                                    fg_color=colors.get(self._current_tab, MacColors.BLUE))

        messagebox.showinfo("WinRA", message)
        if self._reset_timer:
            self.after_cancel(self._reset_timer)
        self._reset_timer = self.after(2000, self._reset_progress)

    def _on_error(self, error_msg):
        self._is_processing = False
        self._progress.set(1.0)
        self._progress.configure(progress_color=MacColors.RED)
        self._progress_label.configure(text="Error", text_color=MacColors.RED)

        labels = {"extract": "Extract", "compress": "Create ZIP", "convert": "Convert"}
        colors = {"extract": MacColors.BLUE, "compress": MacColors.GREEN, "convert": MacColors.PURPLE}
        self._action_btn.configure(state="normal", text=labels.get(self._current_tab, "Go"),
                                    fg_color=colors.get(self._current_tab, MacColors.BLUE))

        messagebox.showerror("WinRA", f"Error:\n\n{error_msg}")
        if self._reset_timer:
            self.after_cancel(self._reset_timer)
        self._reset_timer = self.after(2000, self._reset_progress)

    def _reset_progress(self):
        """Reset progress bar to default state."""
        self._progress.configure(progress_color=MacColors.BLUE)
        self._progress_label.configure(text="Ready", text_color=self.C.TEXT_TERTIARY)
