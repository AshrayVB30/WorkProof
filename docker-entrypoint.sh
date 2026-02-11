#!/bin/bash

# Start Xvfb (Virtual Framebuffer)
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

# Start a simple window manager so windows can be moved/resized
fluxbox &
sleep 2

# Start x11vnc server (passwordless for simplicity in this dev environment)
x11vnc -display :99 -forever -nopw -listen localhost -xkb &
sleep 2

# Start NoVNC to provide web-based access to the GUI
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 &
sleep 2

echo "NoVNC is running at http://localhost:6080/vnc.html"

# Run the Python application
exec python main.py
