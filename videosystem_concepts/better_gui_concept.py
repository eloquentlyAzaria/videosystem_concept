from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Callable, List, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageFilter

@dataclass
class Video:
    id: str
    title: str
    channel: str
    views: int
    age_days: int
    duration: str
    color: Tuple[int, int, int]

_random = random.Random(42)
_palette = [
    (220, 20, 60),
    (65, 105, 225),
    (255, 140, 0),
    (34, 139, 34),
    (123, 104, 238),
    (255, 99, 71),
    (0, 191, 255),
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
_channels = ["CodeGarden", "UI Nerd", "Midnight Dev", "PixelSmith", "The Pythonist", "DesignSense"]

MOCK_VIDEOS: List[Video] = [
    Video(
        id=f"vid_{i}",
        title=_random.choice(_titles),
        channel=_random.choice(_channels),
        views=_random.randint(1_000, 2_500_000),
        age_days=_random.randint(0, 900),
        duration=f"{_random.randint(1, 2)}:{_random.randint(0,59):02d}:{_random.randint(0,59):02d}",
        color=_random.choice(_palette),
    )
    for i in range(24)
]

ASSET_CACHE: dict = {}

def _rounded_shadow_rgba(size: Tuple[int, int], radius: int = 24, shadow: int = 12) -> Image.Image:
    w, h = size
    canvas = Image.new("RGBA", (w + shadow * 2, h + shadow * 2), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    shadow_img = Image.new("RGBA", (w, h), (0, 0, 0, 140))
    canvas.paste(shadow_img, (shadow, shadow), mask)
    canvas = canvas.filter(ImageFilter.GaussianBlur(10))
    return canvas

def _apply_rounded(img: Image.Image, radius: int = 24) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
    img = img.convert("RGBA")
    img.putalpha(mask)
    return img

def make_thumb(text: str, color=(220, 20, 60), size=(480, 270)) -> Image.Image:
    key = (text, color, size)
    if key in ASSET_CACHE:
        return ASSET_CACHE[key]
    base_w, base_h = size
    W, H = base_w * 2, base_h * 2
    img = Image.new("RGB", (W, H), color)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    tri_w = int(W * 0.16)
    tri_h = int(H * 0.20)
    cx, cy = W // 2, H // 2
    points = [(cx - tri_w // 3, cy - tri_h // 2), (cx - tri_w // 3, cy + tri_h // 2), (cx + tri_w, cy)]
    od.polygon(points, fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 56)
    except (OSError, IOError):
        font = ImageFont.load_default()
    def wrap(t: str, max_chars=42):
        words, lines, buf = t.split(), [], []
        for w in words:
            if sum(len(x) for x in buf) + len(buf) - 1 + len(w) > max_chars:
                lines.append(" ".join(buf)); buf = [w]
            else:
                buf.append(w)
        if buf: lines.append(" ".join(buf))
        return "\n".join(lines[:2])
    wrapped = wrap(text)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    x = 32
    y = H - h - 32
    draw.multiline_text((x + 4, y + 4), wrapped, font=font, fill=(0, 0, 0))
    draw.multiline_text((x, y), wrapped, font=font, fill=(255, 255, 255))
    img = _apply_rounded(img, radius=36)
    shadow = _rounded_shadow_rgba((W, H), radius=36, shadow=16)
    canvas = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    canvas.alpha_composite(shadow, (0, 0))
    canvas.alpha_composite(img, (16, 16))
    canvas = canvas.resize((base_w, base_h), Image.LANCZOS)
    ASSET_CACHE[key] = canvas
    return canvas

def fmt_views(v: int) -> str:
    return f"{v/1_000_000:.1f}M views" if v >= 1_000_000 else (f"{v/1_000:.1f}K views" if v >= 1_000 else f"{v} views")

def fmt_age(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    if days < 30:
        return f"{days} days ago"
    m = days // 30
    return f"{m} months ago" if m < 12 else f"{m // 12} years ago"

class RippleButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._base_width = self.cget("width") or 0
        self._base_height = self.cget("height") or 0
        self.bind("<Button-1>", self._pulse, add="+")
    def _pulse(self, _evt=None):
        w0, h0 = self._base_width, self._base_height
        if w0 == 0 or h0 == 0:
            return
        def step(i):
            if i <= 4:
                k = 1 - i * 0.03
                self.configure(width=int(w0 * k), height=int(h0 * k))
                self.after(12, lambda: step(i + 1))
            elif i <= 8:
                k = 1 - (8 - i) * 0.03
                self.configure(width=int(w0 * k), height=int(h0 * k))
                self.after(12, lambda: step(i + 1))
            else:
                self.configure(width=w0, height=h0)
        step(0)

class CategoryChip(ctk.CTkButton):
    def __init__(self, master, text="", **kwargs):
        super().__init__(master, text=text, height=28, corner_radius=14, **kwargs)
        self._font0 = ctk.CTkFont(size=12)
        self._font1 = ctk.CTkFont(size=13)
        self.configure(font=self._font0)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
    def _enter(self, _):
        self.configure(font=self._font1)
    def _leave(self, _):
        self.configure(font=self._font0)

class SlidingSidebar(ctk.CTkFrame):
    def __init__(self, master, grid_host, width=240, **kwargs):
        super().__init__(grid_host, width=width, fg_color=("#0f0f0f", "#0f0f0f"), **kwargs)
        self._grid_host = grid_host
        self._target_width = width
        self._cur = width
        self._visible = True
        self.grid(row=1, column=0, sticky="nsw")
        self._apply_width(width)
    def _apply_width(self, w):
        self._grid_host.grid_columnconfigure(0, minsize=w)
        self.configure(width=w)
    def toggle(self):
        self.slide_to(0 if self._visible else self._target_width)
        self._visible = not self._visible
    def slide_to(self, w_target: int, duration_ms: int = 160):
        steps = 16
        w0 = self._cur
        dw = (w_target - w0) / steps
        i = 0
        def anim():
            nonlocal i
            if i < steps:
                cur = int(w0 + dw * i)
                self._apply_width(cur)
                i += 1
                self.after(duration_ms // steps, anim)
            else:
                self._cur = w_target
                self._apply_width(w_target)
        anim()

class HoverThumb(ctk.CTkButton):
    def __init__(self, master, images: List[Image.Image], command=None, **kwargs):
        self.thumb_size = kwargs.pop("thumb_size", (320, 180))
        super().__init__(master, text="", fg_color="transparent", hover=False, border_width=0, command=command, **kwargs)
        self._frames = [ctk.CTkImage(light_image=im, dark_image=im, size=self.thumb_size) for im in images]
        self._hover_frames = [ctk.CTkImage(light_image=im, dark_image=im, size=(int(self.thumb_size[0]*1.04), int(self.thumb_size[1]*1.04))) for im in images]
        self._hover = False
        self._idx = 0
        self.configure(image=self._frames[0])
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")
        self._cycle_job = None
    def _enter(self, _e=None):
        self._hover = True
        self.configure(image=self._hover_frames[self._idx])
        self._start_cycle()
    def _leave(self, _e=None):
        self._hover = False
        self.configure(image=self._frames[self._idx])
        if self._cycle_job:
            self.after_cancel(self._cycle_job)
            self._cycle_job = None
    def _start_cycle(self):
        def tick():
            self._idx = (self._idx + 1) % len(self._frames)
            self.configure(image=self._hover_frames[self._idx] if self._hover else self._frames[self._idx])
            self._cycle_job = self.after(300, tick)
        if not self._cycle_job:
            self._cycle_job = self.after(300, tick)

class AnimatedProgressBar(ctk.CTkProgressBar):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.set(0.0)
        self._job = None
    def start(self):
        if self._job:
            return
        def anim(val=0.0, direction=1):
            v = val + direction * 0.01
            if v >= 1.0:
                v, direction = 1.0, -1
            if v <= 0.0:
                v, direction = 0.0, 1
            self.set(v)
            self._job = self.after(16, lambda: anim(v, direction))
        anim()
    def stop(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None

class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable[[str], None]):
        super().__init__(master, fg_color=("#181818", "#181818"))
        self.on_search = on_search
        self.menu_btn = RippleButton(self, text="≡", width=44, height=36, corner_radius=10, command=master.toggle_sidebar)
        self.menu_btn.grid(row=0, column=0, padx=(10, 6), pady=10)
        self.logo = ctk.CTkLabel(self, text="SceneHop", font=("Segoe UI", 18, "bold"))
        self.logo.grid(row=0, column=1, padx=(0, 12))
        self.search_var = ctk.StringVar()
        self.search = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Search", height=36, corner_radius=12, width=520)
        self.search.grid(row=0, column=2, sticky="ew")
        self.search.bind("<Return>", lambda _e: self.on_search(self.search_var.get().strip()))
        self.search_btn = RippleButton(self, text="🔎", width=44, height=36, corner_radius=10, command=lambda: self.on_search(self.search_var.get().strip()))
        self.search_btn.grid(row=0, column=3, padx=(6, 6))
        self.mic_btn = RippleButton(self, text="🎤", width=44, height=36, corner_radius=10)
        self.mic_btn.grid(row=0, column=4)
        self.upload_btn = RippleButton(self, text="⬆", width=44, height=36, corner_radius=10)
        self.upload_btn.grid(row=0, column=5, padx=(16, 6))
        self.bell_btn = RippleButton(self, text="🔔", width=44, height=36, corner_radius=10)
        self.bell_btn.grid(row=0, column=6, padx=(6, 6))
        self.avatar = ctk.CTkLabel(self, text="A", width=36, height=36, corner_radius=18, fg_color="#3d3d3d")
        self.avatar.grid(row=0, column=7, padx=(6, 12))
        self.grid_columnconfigure(2, weight=1)

class SideNav(ctk.CTkFrame):
    def __init__(self, master, on_nav: Callable[[str], None]):
        super().__init__(master, fg_color=("#0f0f0f", "#0f0f0f"))
        self.on_nav = on_nav
        ctk.CTkLabel(self, text="Navigation", anchor="w").pack(fill="x", padx=16, pady=(12, 6))
        for emoji, label, key in [
            ("🏠", "Home", "home"),
            ("🎬", "Scenes", "scenes"),
            ("📺", "Subscriptions", "subs"),
            ("📚", "Library", "library"),
            ("🕘", "History", "history"),
            ("❤️", "Liked", "liked"),
        ]:
            RippleButton(self, text=f"{emoji}  {label}", anchor="w", height=40, corner_radius=12, command=lambda k=key: self.on_nav(k)).pack(fill="x", padx=10, pady=4)

class VideoCard(ctk.CTkFrame):
    def __init__(self, master, video: Video, on_open: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        self.video = video
        self.on_open = on_open
        base = make_thumb(video.title, color=video.color, size=(480, 270))
        alt1 = make_thumb(video.title, color=tuple(min(255, int(c * 1.05)) for c in video.color), size=(480, 270))
        alt2 = make_thumb(video.title, color=tuple(max(0, int(c * 0.92)) for c in video.color), size=(480, 270))
        images = [base, alt1, alt2]
        self.thumb_btn = HoverThumb(self, images, thumb_size=(320, 180), command=self._clicked)
        self.thumb_btn.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.badge = ctk.CTkLabel(self.thumb_btn, text=video.duration, fg_color="#000000", text_color="#ffffff")
        self.badge.place(relx=0.98, rely=0.02, anchor="ne")
        self.title = ctk.CTkLabel(self, text=video.title, font=("Segoe UI", 14, "bold"), justify="left")
        self.title.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.meta = ctk.CTkLabel(self, text=f"{video.channel} • {fmt_views(video.views)} • {fmt_age(video.age_days)}", font=("Segoe UI", 12))
        self.meta.grid(row=2, column=0, columnspan=2, sticky="w")
    def _clicked(self):
        self.on_open(self.video)

class VideoGrid(ctk.CTkScrollableFrame):
    def __init__(self, master, on_open: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        self.on_open = on_open
        self.cards: List[VideoCard] = []
        for col in range(4):
            self.columnconfigure(col, weight=1, uniform="cols")
    def populate(self, videos: List[Video]):
        for w in self.cards:
            w.destroy()
        self.cards.clear()
        for i, v in enumerate(videos):
            card = VideoCard(self, v, on_open=self.on_open)
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
        self.geometry("1024x640")
        self.configure(fg_color="#0f0f0f")
        self.bind("<Escape>", lambda _e: self.destroy())
        left = ctk.CTkFrame(self, fg_color="#181818")
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        big_img = make_thumb(video.title, color=video.color, size=(1280, 720))
        big = ctk.CTkImage(light_image=big_img, dark_image=big_img, size=(960, 540))
        ctk.CTkLabel(left, text="", image=big).pack(padx=10, pady=10)
        ctk.CTkLabel(left, text=video.title, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=12)
        ctk.CTkLabel(left, text=f"{video.channel} • {fmt_views(video.views)} • {fmt_age(video.age_days)}").pack(anchor="w", padx=12, pady=(0,10))
        right = ctk.CTkScrollableFrame(self, width=340, fg_color="#0f0f0f")
        right.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        recs = MOCK_VIDEOS[:12]
        for rv in recs:
            thumb = ctk.CTkImage(light_image=make_thumb(rv.title, rv.color, (480,270)), dark_image=make_thumb(rv.title, rv.color, (480,270)), size=(160, 90))
            f = ctk.CTkFrame(right, fg_color="transparent")
            f.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(f, text="", image=thumb, width=160, height=90).grid(row=0, column=0, rowspan=2, sticky="w")
            ctk.CTkLabel(f, text=rv.title, font=("Segoe UI", 12, "bold"), wraplength=160, justify="left").grid(row=0, column=1, sticky="w", padx=8)
            ctk.CTkLabel(f, text=f"{rv.channel}\n{fmt_views(rv.views)} • {fmt_age(rv.age_days)}", justify="left").grid(row=1, column=1, sticky="nw", padx=8)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        ctk.CTkButton(self, text="✕ Close", command=self.destroy).grid(row=1, column=0, columnspan=2, pady=(0,10))

class HomeView(ctk.CTkFrame):
    def __init__(self, master, on_open: Callable[[Video], None]):
        super().__init__(master, fg_color="transparent")
        chipbar = ctk.CTkFrame(self, fg_color="#0f0f0f")
        chipbar.pack(fill="x", padx=10, pady=(10,0))
        for label in ["All", "Music", "Programming", "Live", "News", "Design", "Shorts", "Podcasts"]:
            CategoryChip(chipbar, text=label).pack(side="left", padx=6, pady=6)
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
        self.header = HeaderBar(self, on_search=self._on_search)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.sidebar = SlidingSidebar(self, self, width=240)
        self.sidenav = SideNav(self.sidebar, on_nav=self._on_nav)
        self.sidenav.pack(fill="y", expand=True)
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew")
        self.home = HomeView(self.content, on_open=self._open_video)
        self.home.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize)
    def toggle_sidebar(self):
        self.sidebar.toggle()
    def _on_nav(self, key: str):
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
    def _on_resize(self, _evt=None):
        width = self.winfo_width()
        want_open = width >= 1100
        if want_open and not self.sidebar._visible:
            self.sidebar.toggle()
        elif not want_open and self.sidebar._visible:
            self.sidebar.toggle()

if __name__ == "__main__":
    app = App()
    app.mainloop()
