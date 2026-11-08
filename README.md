# Frutiger OS 1.0 “Lagoon”

A Windows 7/Vista–inspired Linux distribution with a Frutiger Aero look: glossy glass,
sky-and-water wallpapers, bubbles, and a glowing Start orb. It's built on Debian 12 + Xfce
with a custom theme, so it's stable and runs everyday Linux software.

`docs/preview.html` is a clickable browser mock-up of the desktop (open it in any browser).

## What's in it

| Piece | What it does |
|---|---|
| **Frutiger-Aero GTK 3 theme** | Glossy two-tone buttons, Aero selection highlight, glass header bars, red-glow close button, green meters. Built on Adwaita so every widget is covered. |
| **Frutiger-Aero xfwm4 theme** | Translucent glass window frames with Aero caption “caps” (bitmaps made by `tools/gen_assets.py`). |
| **Aero blur** | `picom` with dual-kawase blur behind frames, panel, dock and menus. Falls back to xfwm4's compositor automatically if 3D isn't available. |
| **Twelve taskbar styles** | Switch live in Personalize (pick, *Try it*, Save) or with `frutiger-taskbar <style>`:<br>**Bubble Dock** `dock` (default): Plank with a glass-shelf theme, zoom and bounce.<br>**Orbit Launcher** `orbit`: a corner orb; pinned apps fan out on an inner arc, open windows on an outer arc.<br>**Aquarium Rail** `aquarium`: a water strip; apps are koi: running ones swim, pinned ones rest on the sand.<br>**Leaf Shelf** `leaf`: a glass branch with a leaf per app: idle leaves sway, running ones glow.<br>**Cloud Bar** `cloud`: clouds drift along the top edge; the active one is sunlit gold, one wanting attention rains.<br>**Glass Bead String** `beads`: glass marbles hang across the bottom and swing when the pointer brushes them.<br>**Aurora Ribbon** `ribbon`: icons ride a slowly flowing ribbon of light.<br>**Sundial Clock** `sundial`: a corner clock whose hour markers are your apps; the orb is its centre.<br>**Lily Pond** `pond`: a corner pond with a lily pad per app; running apps bloom a lotus.<br>**Vista Sidebar** `sidebar`: a glass column on the right with a clock, date, CPU/memory gadgets and app tiles.<br>**Flip 3D Carousel** `flip`: nothing on screen; press Super or push the pointer into the bottom-left corner and your windows fan out in a 3D glass stack.<br>**Classic** `classic`: an Aero taskbar with the Start orb (Whisker Menu). |
| **Personalize** | Pick the glass color/intensity, toggle blur, switch taskbar style, and choose app icons: **Consistent set (Papirus)** or **App-provided icons** (each app's own icon; Papirus still covers folders, files and system icons). Applies live to GTK, Qt, the dock and Orbit. |
| **Boot splash** | Plymouth theme: sky-and-water scene, logo floating in an iridescent glass bubble, rising bubbles, glowing progress orbs, styled password prompt. |
| **Living desktop** | `frutiger-desktopd`: wallpaper follows the **time of day** (Lagoon at dawn, midday, sunset, starry night with aurora), or one picture, or a **slideshow** of the 10-scene pack; **live effects** (rising bubbles, ripples) and optional **weather effects** (rain/snow when it's raining/snowing in your city, via Open-Meteo, only contacted when switched on). |
| **Gadgets** | `frutiger-gadgets`: clock, weather, CPU/memory meter, sticky note, photo slideshow (from ~/Pictures), each switchable. |
| **Sounds** | Original synthesized "Frutiger" sound theme: startup chime, water-drop notifications, bubble-pop on close, glassy clicks (optional). Regenerate with `tools/gen_sounds.py`. |
| **Screensaver** | `frutiger-screensaver`: glossy bubbles drifting and bouncing; starts after the idle time you choose (never over fullscreen apps). |
| **Look** | Glossy icon theme (every app icon inside a glass bubble, generated from Papirus + your apps' own icons, refreshed after apt installs), glossy Frutiger cursors with a bead-ring spinner, Selawik font when available (downloaded at build time), glass notification balloons, glass Alt+Tab switcher, Explorer-style breadcrumbs in Thunar, Frutiger Aqua terminal colors, Frutiger Aero Firefox theme. |
| **Welcome Center** | `frutiger-welcome`: opens on first login: a short tour, pick a taskbar style, glass color, wallpaper and gadgets, then quick links. Also in the Start menu. |
| **Boot menu** | GRUB theme (sky scene, logo bubble, glass "Choose how to start" panel, Aero selection) on the USB and installed systems, plus a matching menu for old BIOS PCs. On an installed system the menu is hidden unless another OS (e.g. Windows) is found; press Esc during startup to show it. |
| **Installer** | Calamares with Frutiger branding: blue sidebar, logo, welcome image and a 4-slide slideshow. "Install Frutiger OS" sits on the live desktop. |
| **Login** | LightDM GTK greeter on the Lagoon wallpaper with the Aero theme. |
| **Icons & fonts** | `Frutiger` icon theme (Papirus Light + orb branding), Noto Sans, DMZ-White cursor. |
| **Third-party apps** | Qt 5 apps (VLC, KDE apps) themed via qt5ct + an Aero style sheet; Qt 6 apps (OBS…) via qt6ct, with launchers wrapped automatically after every `apt install`; GTK 2 apps via a Murrine gtkrc; Flatpak apps get the GTK theme and your accent through a system-wide override; Flathub enabled. |
| **Games** | picom steps aside for fullscreen windows (`unredir-if-possible`): no blur cost or extra latency in games and video. |

Switch taskbar styles from Personalize or a terminal:
```
frutiger-taskbar dock | orbit | aquarium | leaf | cloud | beads | ribbon
                 sundial | pond | sidebar | flip | classic
```
All the custom styles share one list of pinned apps. In every strip/corner style: click an app to
open / focus / minimize it (or cycle through its windows), middle-click to close, right-click to
pin or unpin; the orb opens the Start menu (right-click it for Personalize). Edge styles reserve
space so maximized windows stop short of them; Sundial and Lily Pond float in the corner.
**Orbit icons:** open-window bubbles use the same themed icon as the app's pinned bubble, so a
running app looks identical to its pin (falls back to the window's own icon, e.g. for Wine games).

**Orbit pins:** right-click a window bubble to pin its app, right-click a pinned bubble to unpin
(stored in `~/.config/frutiger/orbit-pins`). Middle-click a window bubble to close it.

### Desktop settings (Personalize → Desktop)
Everything is optional and saved in `~/.config/frutiger/desktop.ini`:

| Switch | Default |
|---|---|
| Calm mode: turns off everything that moves, keeps your other choices | off |
| Wallpaper: time of day / one picture / slideshow (+ minutes) | time of day |
| Live effects (bubbles, ripples) | on |
| Weather effects (+ your city) | off |
| Desktop gadgets (master) → clock, weather, CPU meter, sticky note, photo slideshow | on → on, on, on, off, off |
| Frutiger sounds / glassy click sounds | on / off |
| Bubbles screensaver (+ minutes) | on, 10 min |
| Window effects (fades) | on |

Appearance → App icons: **Glossy (Frutiger)** (default), **Consistent set (Papirus)**, **App-provided icons**.

### How third-party apps fit in
Every app shows up in all three taskbar styles automatically (standard X11 window hints); installed
apps appear in the Start menu / *All programs*; tray icons go to the system tray (in Dock/Orbit
it's in the auto-hiding top bar). The Bubble Dock also shows app badges/progress and right-click
actions. What still won't match the Aero look: GTK 4 / libadwaita apps (they ignore custom themes
by design) and apps that draw their own UI (Firefox, Chrome, Electron, Steam) — those still get
the glass window frame.

In every style except Classic the Xfce panel (tray, volume, clock) hides along the top edge: push the pointer to the top to reveal it.

## Build the ISO

You need a Debian 12 machine (a VM is fine) with ~15 GB free space and internet.

```bash
sudo apt install live-build
sudo ./build.sh
```

The build takes 20–60 minutes and produces `frutiger-os-1.0-amd64.hybrid.iso`. Boot it in
VirtualBox/GNOME Boxes/virt-manager (enable 3D acceleration for blur), or write it to a USB stick:

```bash
sudo dd if=frutiger-os-1.0-amd64.hybrid.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Live session user: `aero` (no password).

### Or let GitHub build it for you (no Debian machine needed)

1. Create a new **public** repository on GitHub and upload this folder's contents to it
   (including the hidden `.github` folder).
2. Open the repository's **Actions** tab → **Build Frutiger OS ISO** → **Run workflow**.
3. After 30–90 minutes, open the finished run and download **frutiger-os-iso** under *Artifacts*
   (a zip containing the ISO and its checksum). If it fails, download **build-log** and send it over.

### Try the theme without building an ISO

On an existing Debian/Ubuntu Xfce install:

```bash
sudo apt install plank picom papirus-icon-theme dmz-cursor-theme fonts-noto-core \
     xfce4-whiskermenu-plugin python3-gi gir1.2-wnck-3.0 python3-pil
sudo cp -r config/includes.chroot/usr/* /usr/
sudo cp -r config/includes.chroot/etc/xdg/* /etc/xdg/
sudo cp -r config/includes.chroot/etc/dconf/* /etc/dconf/ && sudo dconf update
cp -r config/includes.chroot/etc/skel/.config/* ~/.config/   # overwrites your Xfce panel/settings!
```
Then log out and back in.

## Layout

```
build.sh                      live-build wrapper
config/package-lists/         packages in the image
config/hooks/normal/          build-time setup (plymouth, dconf, branding)
config/includes.chroot/       files copied into the image
  usr/share/themes/Frutiger-Aero/   GTK 3 + xfwm4 theme
  usr/share/plymouth/themes/frutiger/ boot splash
  usr/share/plank/themes/Frutiger-Bubble/ Bubble Dock theme
  usr/bin/frutiger-*          the taskbar styles, personalize, taskbar switcher, session setup
  usr/lib/frutiger/frutiger_strip.py  shared engine for the strip and corner styles
  etc/skel/.config/           default user desktop (panel, wm, settings, dock items)
tools/gen_assets.py           regenerate window-frame bitmaps in any tint
tools/splash.html, bubble-logo.svg  sources for the boot splash art
tools/grub-bg.html, installer-slides.html  sources for the boot menu and installer art
tools/wallpapers.html         the wallpaper pack (open with #lagoon-day, #aquarium, … and screenshot)
tools/gen_sounds.py, gen_cursors.py  synthesize the sound theme, draw the cursor theme
config/hooks/normal/*.hook.binary       brands the ISO's boot menus
docs/preview.html             interactive browser preview
```

## Status / next steps

- The config files and scripts have been syntax-checked, but the ISO hasn't been built or
  booted yet. Expect a round of fixes on the first real build. The Orbit Launcher in
  particular should be tested on a real Xfce session.
- The Bubble Dock on Linux uses Plank: you get the glass shelf, zoom and bounce, but not
  the separate soap bubble around each icon from the preview. Getting that look means a
  small custom dock (it can reuse the Orbit Launcher's bubble drawing code).
- Flatpak apps get the GTK theme but not the Frutiger icon theme (Papirus is too large to copy into
  every home folder); they fall back to their own bundled icons.
- Window effects on Debian 12 are fades only: picom 10 has no open/minimize animations (picom 12,
  in Debian 13, does). The preview shows the intended bubble animations.
- The glossy icon theme is generated automatically; a few unusual app icons may look off in a bubble.
  Switch to Papirus or App-provided icons in Personalize if so.
- Ideas: Calamares branding slideshow, GRUB theme, matching GTK 4/libadwaita accent,
  sound theme, a custom icon set, desktop gadgets (Conky).

Not affiliated with Microsoft. “Frutiger Aero” refers to the design style, not the typeface.
