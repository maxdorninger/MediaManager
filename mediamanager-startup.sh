#!/usr/bin/env bash
set -eEuo pipefail # fail if any errors are encountered

# This script is used to start the MediaManager service.


# text created with https://patorjk.com/software/taag/ font: Slanted
display_cool_text() {
  local ascii_art="$1"

  local r_blue=80
  local g_blue=100
  local b_blue=230

  local r_orange=255
  local g_orange=140
  local b_orange=80

  local r_red=230
  local g_red=40
  local b_red=70

  local max_width=0
  while IFS= read -r line; do
    local line_length=${#line}
    if (( line_length > max_width )); then
      max_width=$line_length
    fi
  done <<< "$ascii_art"

  while IFS= read -r line; do
    local length=${#line}

    if [[ $length -eq 0 ]]; then
      echo ""
      continue
    fi

    local seg1=$((max_width / 2))

    for (( i=0; i<length; i++ )); do
      local char="${line:$i:1}"

      local r=0
      local g=0
      local b=0

      if (( i < seg1 )); then
        local percentage=$(echo "scale=2; $i / $seg1" | bc)
        r=$(echo "scale=0; $r_blue + ($r_orange - $r_blue) * $percentage" | bc | cut -d. -f1)
        g=$(echo "scale=0; $g_blue + ($g_orange - $g_blue) * $percentage" | bc | cut -d. -f1)
        b=$(echo "scale=0; $b_blue + ($b_orange - $b_blue) * $percentage" | bc | cut -d. -f1)
      else
        local segment_pos=$(( i - seg1 ))
        local segment_length=$(( max_width - seg1 ))
        if [[ $segment_length -eq 0 ]]; then
          segment_length=1
        fi
        local percentage=$(echo "scale=2; $segment_pos / $segment_length" | bc)
        r=$(echo "scale=0; $r_orange + ($r_red - $r_orange) * $percentage" | bc | cut -d. -f1)
        g=$(echo "scale=0; $g_orange + ($g_red - $g_orange) * $percentage" | bc | cut -d. -f1)
        b=$(echo "scale=0; $b_orange + ($b_red - $b_orange) * $percentage" | bc | cut -d. -f1)
      fi

      [[ $r -lt 0 ]] && r=0
      [[ $r -gt 255 ]] && r=255
      [[ $g -lt 0 ]] && g=0
      [[ $g -gt 255 ]] && g=255
      [[ $b -lt 0 ]] && b=0
      [[ $b -gt 255 ]] && b=255

      if [[ "$char" == " " ]]; then
        printf " "
      else
        printf "\033[38;2;%d;%d;%dm%s\033[0m" $r $g $b "$char"
      fi
    done
    printf "\n"
  done <<< "$ascii_art"
}
ASCII_ART='

 ██████   ██████              █████  ███
░░██████ ██████              ░░███  ░░░
 ░███░█████░███   ██████   ███████  ████   ██████
 ░███░░███ ░███  ███░░███ ███░░███ ░░███  ░░░░░███
 ░███ ░░░  ░███ ░███████ ░███ ░███  ░███   ███████
 ░███      ░███ ░███░░░  ░███ ░███  ░███  ███░░███
 █████     █████░░██████ ░░████████ █████░░████████
░░░░░     ░░░░░  ░░░░░░   ░░░░░░░░ ░░░░░  ░░░░░░░░



 ██████   ██████
░░██████ ██████
 ░███░█████░███   ██████   ████████    ██████    ███████  ██████  ████████
 ░███░░███ ░███  ░░░░░███ ░░███░░███  ░░░░░███  ███░░███ ███░░███░░███░░███
 ░███ ░░░  ░███   ███████  ░███ ░███   ███████ ░███ ░███░███████  ░███ ░░░
 ░███      ░███  ███░░███  ░███ ░███  ███░░███ ░███ ░███░███░░░   ░███
 █████     █████░░████████ ████ █████░░████████░░███████░░██████  █████
░░░░░     ░░░░░  ░░░░░░░░ ░░░░ ░░░░░  ░░░░░░░░  ░░░░░███ ░░░░░░  ░░░░░
                                                ███ ░███
                                               ░░██████
                                                ░░░░░░

'
if [[ -v MEDIAMANAGER_NO_STARTUP_ART ]]; then
  echo
  echo "   +================+"
  echo "   |  MediaManager  |"
  echo "   +================+"
  echo
else
  display_cool_text "$ASCII_ART"
fi

echo "Buy me a coffee at https://buymeacoffee.com/maxdorninger"

# Initialize config if it doesn't exist
CONFIG_DIR=${CONFIG_DIR:-/app/config}
CONFIG_FILE="$CONFIG_DIR/config.toml"
EXAMPLE_CONFIG="/app/config.example.toml"

echo "Checking configuration setup..."

# Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating config directory: $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
fi

# Copy example config if config.toml doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found. Copying example config to: $CONFIG_FILE"
    if [ -f "$EXAMPLE_CONFIG" ]; then
        cp "$EXAMPLE_CONFIG" "$CONFIG_FILE"
        echo "Example config copied successfully!"
        echo "Please edit $CONFIG_FILE to configure MediaManager for your environment."
        echo "Important: Make sure to change the token_secret value!"
    else
        echo "ERROR: Example config file not found at $EXAMPLE_CONFIG"
        exit 1
    fi
else
    echo "Config file found at: $CONFIG_FILE"
fi

# check if running as root, if yes, fix permissions
if [ "$(id -u)" = '0' ]; then
    echo "Running as root. Ensuring file permissions for mediamanager user..."
    chown -R mediamanager:mediamanager "$CONFIG_DIR"

    if [ -d "/data" ]; then
        if [ "$(stat -c '%U' /data)" != "mediamanager" ]; then
            echo "Fixing ownership of /data (this may take a while for large media libraries)..."
            chown -R mediamanager:mediamanager /data
        else
            echo "/data ownership is already correct."
        fi
    fi
else
    echo "Running as non-root user ($(id -u)). Skipping permission fixes."
    echo "Note: Ensure your host volumes are manually set to the correct permissions."
fi

echo "Running DB migrations..."
if [ "$(id -u)" = '0' ]; then
   gosu mediamanager uv run alembic upgrade head
else
   uv run alembic upgrade head
fi

echo "Starting MediaManager backend service..."
echo ""
echo "   LOGIN INFORMATION:"
echo "   If this is a fresh installation, a default admin user will be created automatically."
echo "   Check the application logs for the login credentials."
echo "   You can also register a new user and it will become admin if the email"
echo "   matches one of the admin_emails in your config.toml"
echo ""

DEVELOPMENT_MODE=${MEDIAMANAGER_MISC__DEVELOPMENT:-FALSE}
PORT=${PORT:-8000}

if [ "$DEVELOPMENT_MODE" == "TRUE" ]; then
    echo "Development mode is enabled, enabling auto-reload..."
    DEV_OPTIONS="--reload"
else
    DEV_OPTIONS=""
fi

if [ "$(id -u)" = '0' ]; then
    exec gosu mediamanager uv run fastapi run /app/media_manager/main.py --port "$PORT" --proxy-headers $DEV_OPTIONS
else
    exec uv run fastapi run /app/media_manager/main.py --port "$PORT" --proxy-headers $DEV_OPTIONS
fi