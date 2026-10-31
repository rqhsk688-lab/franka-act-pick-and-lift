#!/bin/bash
set -e

# ROS 2 Jazzy environment
source /opt/ros/jazzy/setup.bash

# Gazebo GUI display
export DISPLAY=:1

# Qt runtime directory
export XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

mkdir -p /root/.vnc

# VNC接続用パスワードを対話的に入力
read -r -s -p "VNC password (exactly 8 characters): " VNC_PASSWORD
printf '\n'

if [ "${#VNC_PASSWORD}" -ne 8 ]; then
    echo "Error: VNC password must be exactly 8 characters."
    exit 1
fi

# TigerVNC用のパスワードファイルを作成
printf '%s\n' "$VNC_PASSWORD" \
    | tigervncpasswd -f > /root/.vnc/passwd

chmod 600 /root/.vnc/passwd
unset VNC_PASSWORD

# 仮想ディスプレイ :1 を起動
tigervncserver :1 \
    -geometry 1280x800 \
    -depth 24 \
    -localhost yes \
    -SecurityTypes VncAuth

# ブラウザ用のHTTP/WebSocketサーバーを起動
exec websockify --web=/usr/share/novnc 6080 localhost:5901

