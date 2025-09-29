# birthday_flower_better.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import PillowWriter
import colorsys
import tempfile, os, base64

st.set_page_config(page_title="Happy Birthday!", page_icon="🌸", layout="centered")

# ------------------ Customize this ------------------
HER_NAME = "Cleary"   # change to her name if you want
# ----------------------------------------------------

st.title(f"🎉💐 Happy Birthday, {HER_NAME}! 💐🎉")
st.markdown("## A little blooming surprise — made with love 💖")
st.write("Even from far away, I wanted to make something that blooms for you 🌸")

# --- geometry + fig setup ---
theta = np.linspace(0, 2 * np.pi, 1600)
fig, ax = plt.subplots(figsize=(5,7))
ax.set_xlim(-3, 3)
ax.set_ylim(-4, 4)
ax.axis("off")

# helper: hsv -> hex
def hsv_to_hex(h, s=0.75, v=0.97):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return '#%02x%02x%02x' % (int(255*r), int(255*g), int(255*b))

# petal shape via rose-like modulation (smooth, many petals)
def petal_coords(k, scale, rot=0.0):
    r = (1.0 + 0.85 * np.cos(k * (theta + rot)))  # base rose curve
    x = r * np.cos(theta) * scale
    y = r * np.sin(theta) * scale + 1.4  # lift petals above stem
    return x, y

# center "seed" dots
def draw_center(ax, t, seed_count=250):
    # jittered seeds inside small radius, subtly pulsing
    rng = np.random.RandomState(123)  # deterministic
    rs = 0.25 * (1 + 0.12 * np.sin(t * 2.0))
    angles = rng.rand(seed_count) * 2 * np.pi
    radii = (rng.rand(seed_count) ** 0.7) * rs
    xs = radii * np.cos(angles)
    ys = radii * np.sin(angles) + 1.4
    ax.scatter(xs, ys, s=8, c='#6b3e1b', alpha=0.95, linewidths=0)

# stem curve function (swaying)
def stem_coords(frame, frames):
    t = np.linspace(0, 1, 120)
    sway = 0.25 * np.sin(2 * np.pi * frame / frames)  # left-right sway
    # cubic-ish curve from y=1.5 down to -3
    xs = sway * np.sin(np.pi * t) * (1 - 0.3 * t)
    ys = 1.5 + (t - 1) * 4.5  # linear-ish downward
    return xs, ys

# leaf polygon (elliptical) positioned along the stem
def leaf_coords(frame, frames):
    # leaf breath (open/close a bit)
    breath = 0.35 + 0.12 * np.sin(2 * np.pi * frame / frames + 0.5)
    # base center of leaf along stem
    cx = -0.4 + 0.12 * np.sin(2 * np.pi * frame / frames)
    cy = -1.0
    t = np.linspace(0, 2*np.pi, 80)
    rx = 0.7 * breath
    ry = 0.28 * breath
    # rotate slightly
    angle = -0.5 + 0.2 * np.sin(2 * np.pi * frame / frames)
    x = cx + rx * np.cos(t) * np.cos(angle) - ry * np.sin(t) * np.sin(angle)
    y = cy + rx * np.cos(t) * np.sin(angle) + ry * np.sin(t) * np.cos(angle)
    return x, y

# --- Animation function ---
frames = 90
petal_k = 14   # number of petal lobes (higher -> more petals)
layers = 6     # layered fills for depth/gradient effect

def animate(i):
    ax.clear()
    ax.set_xlim(-3, 3)
    ax.set_ylim(-4, 4)
    ax.axis("off")
    t = i / frames

    # bloom scale (0..1..0) smooth
    bloom = 0.15 + 0.85 * (0.5 + 0.5 * np.sin(2 * np.pi * t - np.pi/2))
    # rotation of petals for subtle motion
    rotation = (2 * np.pi * t) * 0.12

    # draw layered petals (outer -> inner) to create gradient depth
    base_hue = 0.95  # pinkish hue; change for different flower color
    for layer in range(layers, 0, -1):
        layer_scale = 0.80 + 0.28 * (layer / layers)
        k = petal_k + (layer % 2)  # slight odd/even variation
        x, y = petal_coords(k=k, scale=layer_scale * bloom * 1.6, rot=rotation + layer * 0.02)
        # color varies slightly by layer (slightly different hue/value)
        hue = base_hue - 0.02 * layer
        col = hsv_to_hex(hue, s=0.65, v=0.98 - layer*0.03)
        alpha = 0.95 - layer * 0.10
        ax.fill(x, y, facecolor=col, edgecolor=None, alpha=max(alpha, 0.12))

    # petal outlines (thin)
    xo, yo = petal_coords(k=petal_k, scale=bloom * 1.6, rot=rotation)
    ax.plot(xo, yo, color="#9b2b6c", linewidth=1.25, alpha=0.9)

    # center seeds / core
    draw_center(ax, t, seed_count=350)

    # stem
    sx, sy = stem_coords(i, frames)
    ax.plot(sx, sy, color="#1f6f2b", linewidth=6, solid_capstyle='round')

    # leaf
    lx, ly = leaf_coords(i, frames)
    ax.fill(lx, ly, color="#2e8b3a", alpha=0.9)

    # little heart in the center (optional tiny pulse)
    heart_scale = 0.4 + 0.12 * np.sin(2 * np.pi * t * 1.8)
    ax.text(0, 1.45, "❤", fontsize=22 * heart_scale, ha="center", va="center", color="#ff6fa3", alpha=0.95)

    # subtle caption
    ax.text(0, -3.6, f"Happy Birthday, {HER_NAME}", fontsize=14, ha="center", va="center")

    return []

# build animation
ani = animation.FuncAnimation(
    fig, animate, frames=frames, interval=50, blit=False, repeat=True, save_count=frames
)

# --- save to temporary GIF file and embed for Streamlit ---
with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as tmpfile:
    tmpname = tmpfile.name
writer = PillowWriter(fps=20)
ani.save(tmpname, writer=writer)   # must pass filename, not BytesIO

# read -> base64 -> show
with open(tmpname, "rb") as f:
    data = f.read()
b64 = base64.b64encode(data).decode("utf-8")
os.remove(tmpname)
plt.close(fig)

st.markdown(f'<img src="data:image/gif;base64,{b64}" width="420">', unsafe_allow_html=True)

st.markdown("---")
st.subheader("💌 A little note for you:")
st.write(
    "Distance means so little when someone means so much. "
    "I hope this tiny bloom brings a smile to your face today — happy birthday 💕"
)
