FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

# 軽量デスクトップ、VNCサーバー、ブラウザ接続用ソフトウェア
RUN apt-get update && apt-get install -y --no-install-recommends \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    tigervnc-standalone-server \
    tigervnc-tools \
    novnc \
    websockify \
    xfonts-base \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Set up ROS 2 and Gazebo environment for interactive shells
RUN printf '%s\n' \
    'source /opt/ros/jazzy/setup.bash' \
    'export DISPLAY=:1' \
    'export XDG_RUNTIME_DIR=/tmp/runtime-root' \
    'mkdir -p "$XDG_RUNTIME_DIR"' \
    'chmod 700 "$XDG_RUNTIME_DIR"' \
    >> /root/.bashrc

# VNCデスクトップの設定
RUN mkdir -p /root/.vnc && \
    printf '%s\n' \
      '$session = "xfce";' \
      '$geometry = "1280x800";' \
      '$depth = "24";' \
      '$localhost = "yes";' \
      '$SecurityTypes = "VncAuth";' \
      > /root/.vnc/tigervnc.conf

# 起動スクリプト
COPY docker/start-vnc.sh /usr/local/bin/start-vnc.sh
RUN chmod +x /usr/local/bin/start-vnc.sh

CMD ["/usr/local/bin/start-vnc.sh"]
