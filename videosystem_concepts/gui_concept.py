"""
YouTube‑style GUI built with customtkinter
-------------------------------------------------
Run with:  python youtube_gui.py

Notes
- Purely local demo (no network).
- Resizes nicely; try dragging the window edges.
- Click any video card to open a mock "watch" view.
- Press Esc or the X in the player to close the watch view.
- If you don’t have customtkinter:  pip install customtkinter pillow
"""

import os
import sys
import random
import datetime as dt
from dataclasses import dataclass
from typing import Callable, List

try:
    import customtkinter as ctk
except Exception as e:
    raise SystemExit("customtkinter is required. Install with: pip install customtkinter pillow\n" + str(e))

from PIL import Image, ImageDraw, ImageFont

# ----------------------
# Mock data structures
# ----------------------
@dataclass
class Video:
    id: str
    title: str
    channel: str
    views: int
    age_days: int
    duration: str
    color: tuple  # RGB for placeholder thumbnail tint


MOCK_VIDEOS: List[Video] = []
_random = random.Random(42)
_palette = [
    (220, 20, 60),   # crimson
    (65, 105, 225),  # royal blue
    (255, 140, 0),   # dark orange
    (34, 139, 34),   # forest green
    (123, 104, 238), # medium slate blue
    (255, 99, 71),   # tomato
    (0, 191, 255),   # deep sky blue
]
_titles = [
    "How to Build a Python GUI Like YouTube",
    "10 CustomTkinter Tips You Need",
    "Lofi Beats to Code/Study To — 3 Hours",
    "The Secret History of GUIs",
    "I Recreated YouTube in 200 Lines (Kinda)",
    "Designing Dark Mode the Right Way",
    "Keyboard Shortcuts that Change Everything",
    "Productivity Myths Busted!",
    "Learn PIL in 15 Minutes",
    "My Desk Setup 2025 — Minimal & Clean",
]
_channels = [
    "CodeGarden",
    "UI Nerd",
    "Midnight Dev",
    "PixelSmith",
    "The Pythonist",
    "DesignSense",
]
for i in range(24):
    MOCK_VIDEOS.append(
        Video(
            id=f"vid_{i}",
            title=_random.choice(_titles),
            channel=_random.choice(_channels),
            views=_random.randint(1_000, 2_500_000),
            age_days=_random.randint(0, 900),
            duration=f"{_random.randint(1, 2)}:{_random.randint(0,59):02d}:{_random.randint(0,59):02d}",
            color=_random.choice(_palette),
        )
    )

# ----------------------
# Helper: thumbnail factory
# ----------------------
ASSET_CACHE = {}

def make_thumb(text: str, color=(220, 20, 60), size=(480, 270)):
    key = (text, color, size)
    if key in ASSET_CACHE:
        return ASSET_CACHE[key]
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    # Semi-transparent play triangle
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    tri_w = int(size[0] * 0.16)
    tri_h = int(size[1] * 0.20)
    cx, cy = size[0] // 2, size[1] // 2
    points = [(cx - tri_w // 3, cy - tri_h // 2), (cx - tri_w // 3, cy + tri_h // 2), (cx + tri_w, cy)]
    od.polygon(points, fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Title text (fit with wrap)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except Exception:
        font = ImageFont.load_default()

    def wrap(t: str, max_chars=24):
        words = t.split()
        lines = []
        buf = []
        for w in words:
            if sum(len(x) for x in buf) + len(buf) - 1 + len(w) > max_chars:
                lines.append(" ".join(buf))
                buf = [w]
            else:
                buf.append(w)
        if buf:
            lines.append(" ".join(buf))
        return "\n".join(lines[:2])

    wrapped = wrap(text)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0

    x = 16
    y = size[1] - h - 16

    # Text shadow
    draw.multiline_text((x+2, y+2), wrapped, font=font, fill=(0,0,0))
    draw.multiline_text((x, y), wrapped, font=font, fill=(255,255,255))

    return_img = img
    ASSET_CACHE[key] = return_img
    return return_img


def fmt_views(v: int) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M views"
    if v >= 1_000:
        return f"{v/1_000:.1f}K views"
    return f"{v} views"


def fmt_age(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    if days < 30:
        return f"{days} days ago"
    months = days // 30
    if months < 12:
        return f"{months} months ago"
    years = months // 12
    return f"{years} years ago"

# ----------------------
# Core UI Components
# ----------------------
class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable[[str], None]):
        super().__init__(master, fg_color=("#181818", "#181818"))
        self.on_search = on_search

        # Left: logo burger
        self.menu_btn = ctk.CTkButton(self, text="≡", width=44, height=36, corner_radius=10, command=self._toggle_menu)
        self.menu_btn.grid(row=0, column=0, padx=(10, 6), pady=10)

        self.logo = ctk.CTkLabel(self, text="SceneHop", font=("Segoe UI", 18, "bold"))
        self.logo.grid(row=0, column=1, padx=(0, 12))

        # Center: search
        self.search_var = ctk.StringVar()
        self.search = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Search", height=36, corner_radius=12, width=520)
        self.search.grid(row=0, column=2, sticky="ew")
        self.search.bind("<Return>", lambda e: self.on_search(self.search_var.get().strip()))

        self.search_btn = ctk.CTkButton(self, text="🔎", width=44, height=36, corner_radius=10,
                                        command=lambda: self.on_search(self.search_var.get().strip()))
        self.search_btn.grid(row=0, column=3, padx=(6, 6))

        self.mic_btn = ctk.CTkButton(self, text="🎤", width=44, height=36, corner_radius=10)
        self.mic_btn.grid(row=0, column=4)

        # Right: user actions
        self.upload_btn = ctk.CTkButton(self, text="⬆", width=44, height=36, corner_radius=10)
        self.upload_btn.grid(row=0, column=5, padx=(16, 6))

        self.bell_btn = ctk.CTkButton(self, text="🔔", width=44, height=36, corner_radius=10)
        self.bell_btn.grid(row=0, column=6, padx=(6, 6))

        self.avatar = ctk.CTkLabel(self, text="A", width=36, height=36, corner_radius=18, fg_color="#3d3d3d")
        self.avatar.grid(row=0, column=7, padx=(6, 12))

        self.grid_columnconfigure(2, weight=1)

    def _toggle_menu(self):
        self.master.toggle_sidebar()


class SideBar(ctk.CTkFrame):
    def __init__(self, master, on_nav: Callable[[str], None]):
        super().__init__(master, width=240, fg_color=("#0f0f0f", "#0f0f0f"))
        self.on_nav = on_nav
        self.collapsed = False
        self._make_items()

    def _item(self, label: str, key: str):
        btn = ctk.CTkButton(
            self, text=f" {label}", anchor="w", height=40, corner_radius=12,
            command=lambda k=key: self.on_nav(k)
        )
        btn.pack(fill="x", padx=10, pady=4)
        return btn

    def _make_items(self):
        self.title = ctk.CTkLabel(self, text="Navigation", anchor="w")
        self.title.pack(fill="x", padx=16, pady=(12, 6))
        self.home = self._item("Home", "home")
        self.scenes = self._item("Scenes", "scenes")
        self.subs = self._item("Subscriptions", "subs")
        self.lib = self._item("Library", "library")
        self.hist = self._item("History", "history")
        self.liked = self._item("Liked", "liked")


    def set_collapsed(self, collapsed: bool):
        if self.collapsed == collapsed:
            return
        self.collapsed = collapsed
        for child in self.winfo_children():
            child.destroy()
        if collapsed:
            for emoji, key in [("🏠","home"),("📺","subs"),("📚","library"),("🕘","history"),("❤️","liked")]:
                ctk.CTkButton(self, text=emoji, width=48, height=48, corner_radius=16,
                              command=lambda k=key: self.on_nav(k)).pack(padx=8, pady=6)
        else:
            self._make_items()


class VideoCard(ctk.CTkFrame):
    def __init__(self, master, video: Video, on_click: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        self.video = video
        self.on_click = on_click

        # Thumbnail
        img = make_thumb(video.title, color=video.color)
        self.thumb_img = ctk.CTkImage(light_image=img, dark_image=img, size=(320, 180))
        self.thumb_btn = ctk.CTkButton(self, text="", image=self.thumb_img, width=320, height=180,
                                       corner_radius=12, command=self._clicked)
        self.thumb_btn.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Duration badge (top-right)
        self.badge = ctk.CTkLabel(self, text=video.duration, fg_color="#000000", text_color="#ffffff")
        self.badge.place(relx=0.98, rely=0.02, anchor="ne")

        # Title and meta
        self.title = ctk.CTkLabel(self, text=video.title, font=("Segoe UI", 14, "bold"), justify="left")
        self.title.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.meta = ctk.CTkLabel(self, text=f"{video.channel} • {fmt_views(video.views)} • {fmt_age(video.age_days)}",
                                 font=("Segoe UI", 12))
        self.meta.grid(row=2, column=0, columnspan=2, sticky="w")

    def _clicked(self):
        self.on_click(self.video)


class VideoGrid(ctk.CTkScrollableFrame):
    def __init__(self, master, on_open: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        self.on_open = on_open
        self.cards: List[VideoCard] = []
        self.columnconfigure((0, 1, 2, 3), weight=1, uniform="cols")

    def populate(self, videos: List[Video]):
        # Clear existing
        for w in self.cards:
            w.destroy()
        self.cards.clear()
        for i, v in enumerate(videos):
            card = VideoCard(self, v, on_click=self.on_open)
            col = i % 4
            row = i // 4
            card.grid(row=row, column=col, padx=10, pady=12, sticky="nsew")
            self.cards.append(card)

    def filter(self, query: str):
        q = query.lower()
        visible = [v for v in MOCK_VIDEOS if q in v.title.lower() or q in v.channel.lower()]
        self.populate(visible)


class PlayerOverlay(ctk.CTkToplevel):
    def __init__(self, master, video: Video):
        super().__init__(master)
        self.title(video.title)
        self.attributes("-topmost", True)
        self.geometry("1024x640")
        self.configure(fg_color="#0f0f0f")
        self.bind("<Escape>", lambda e: self.destroy())

        # Fake player left panel
        left = ctk.CTkFrame(self, fg_color="#181818")
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # large thumbnail as video area
        img = make_thumb(video.title, color=video.color, size=(1280, 720))
        big = ctk.CTkImage(light_image=img, dark_image=img, size=(960, 540))
        ctk.CTkLabel(left, text="", image=big).pack(padx=10, pady=10)

        ctk.CTkLabel(left, text=video.title, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=12)
        ctk.CTkLabel(left, text=f"{video.channel} • {fmt_views(video.views)} • {fmt_age(video.age_days)}").pack(anchor="w", padx=12, pady=(0,10))

        # Right sidebar: recommendations
        right = ctk.CTkScrollableFrame(self, width=340, fg_color="#0f0f0f")
        right.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)

        recs = MOCK_VIDEOS[:12]
        for rv in recs:
            thumb = ctk.CTkImage(light_image=make_thumb(rv.title, rv.color, (320,180)),
                                  dark_image=make_thumb(rv.title, rv.color, (320,180)), size=(160, 90))
            f = ctk.CTkFrame(right, fg_color="transparent")
            f.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(f, text="", image=thumb, width=160, height=90).grid(row=0, column=0, rowspan=2, sticky="w")
            ctk.CTkLabel(f, text=rv.title, font=("Segoe UI", 12, "bold"), wraplength=160, justify="left").grid(row=0, column=1, sticky="w", padx=8)
            ctk.CTkLabel(f, text=f"{rv.channel}\n{fmt_views(rv.views)} • {fmt_age(rv.age_days)}", justify="left").grid(row=1, column=1, sticky="nw", padx=8)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Close button
        ctk.CTkButton(self, text="✕ Close", command=self.destroy).grid(row=1, column=0, columnspan=2, pady=(0,10))


class HomeView(ctk.CTkFrame):
    def __init__(self, master, on_open: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        self.on_open = on_open
        # Filter row (chips)
        chipbar = ctk.CTkFrame(self, fg_color="#0f0f0f")
        chipbar.pack(fill="x", padx=10, pady=(10,0))
        for label in ["All", "Music", "Programming", "Live", "News", "Design", "Shorts", "Podcasts"]:
            ctk.CTkButton(chipbar, text=label, height=28, corner_radius=14).pack(side="left", padx=6, pady=6)

        # Grid of videos
        self.grid_v = VideoGrid(self, on_open=on_open)
        self.grid_v.pack(fill="both", expand=True, padx=6, pady=6)
        self.grid_v.populate(MOCK_VIDEOS)

    def search(self, query: str):
        self.grid_v.filter(query)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("SceneHop")
        self.geometry("1280x800")
        self.minsize(980, 600)

        # Layout: Header, Sidebar, Content
        self.header = HeaderBar(self, on_search=self._on_search)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.sidebar = SideBar(self, on_nav=self._on_nav)
        self.sidebar.grid(row=1, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew")

        self.home = HomeView(self.content, on_open=self._open_video)
        self.home.pack(fill="both", expand=True)

        # Grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Responsive: collapse sidebar under 1100px width
        self.bind("<Configure>", self._on_resize)

    # ----------------------
    # Event handlers
    # ----------------------
    def toggle_sidebar(self):
        self.sidebar.set_collapsed(not self.sidebar.collapsed)

    def _on_nav(self, key: str):
        # For demo, just print and maybe filter
        if key == "home":
            self.home.grid_v.populate(MOCK_VIDEOS)
        elif key == "subs":
            self.home.grid_v.populate(MOCK_VIDEOS[:12])
        elif key == "library":
            self.home.grid_v.populate(list(reversed(MOCK_VIDEOS)))
        elif key == "history":
            self.home.grid_v.populate(MOCK_VIDEOS[6:18])
        elif key == "liked":
            self.home.grid_v.populate(sorted(MOCK_VIDEOS, key=lambda v: v.views, reverse=True)[:12])

    def _on_search(self, query: str):
        self.home.search(query)

    def _open_video(self, video: Video):
        PlayerOverlay(self, video)

    def _on_resize(self, event):
        width = self.winfo_width()
        self.sidebar.set_collapsed(width < 1100)


if __name__ == "__main__":
    app = App()
    app.mainloop()
