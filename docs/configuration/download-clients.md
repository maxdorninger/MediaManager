# Download Clients

Download client settings are configured in the `[torrents]` section of your `config.toml` file. MediaManager supports both qBittorrent and SABnzbd as download clients.

## qBittorrent Settings (`[torrents.qbittorrent]`)

qBittorrent is a popular BitTorrent client that MediaManager can integrate with for downloading torrents.

* `enabled`\
  Set to `true` to enable qBittorrent integration. Default is `false`.
* `host`\
  Hostname or IP of the qBittorrent server. Include the protocol (http/https).
* `port`\
  Port of the qBittorrent Web UI/API. Default is `8080`.
* `username`\
  Username for qBittorrent Web UI authentication. Default is `admin`.
* `password`\
  Password for qBittorrent Web UI authentication. Default is `admin`.

## Transmission Settings (`[torrents.transmission]`)

{% hint style="info" %}
The downloads path in Transmission and MediaManager must be the same, i.e. the path `/data/torrents` must link to the same volume for both containers.
{% endhint %}

Transmission is a BitTorrent client that MediaManager can integrate with for downloading torrents.

* `enabled`\
  Set to `true` to enable Transmission integration. Default is `false`.
* `username`\
  Username for Transmission RPC authentication.
* `password`\
  Password for Transmission RPC authentication.
* `https_enabled`\
  Set to `true` if your Transmission RPC endpoint uses HTTPS. Default is `true`.
* `host`\
  Hostname or IP of the Transmission server (without protocol).
* `port`\
  Port of the Transmission RPC endpoint. Default is `9091`.
* `path`\
  RPC request path target. Usually `/transmission/rpc`.

## SABnzbd Settings (`[torrents.sabnzbd]`)

SABnzbd is a Usenet newsreader that MediaManager can integrate with for downloading NZB files.

* `enabled`\
  Set to `true` to enable SABnzbd integration. Default is `false`.
* `host`\
  Hostname or IP of the SABnzbd server, it needs to include `http(s)://`.
* `port`\
  Port of the SABnzbd API. Default is `8080`.
* `api_key`\
  API key for SABnzbd. You can find this in SABnzbd's configuration under "General" → "API Key".
* `base_path`\
  API base path for SABnzbd. It usually ends with `/api`, the default is `/api`.

## Example Configuration

Here's a complete example of the download clients section in your `config.toml`:

{% code title="config.toml" %}
```toml
[torrents]
    # qBittorrent configuration
    [torrents.qbittorrent]
    enabled = true
    host = "http://qbittorrent"
    port = 8080
    username = "admin"
    password = "your_secure_password"

    # Transmission configuration
    [torrents.transmission]
    enabled = false
    username = "admin"
    password = "your_secure_password"
    https_enabled = true
    host = "transmission"
    port = 9091
    path = "/transmission/rpc"

    # SABnzbd configuration
    [torrents.sabnzbd]
    enabled = false
    host = "http://sabnzbd"
    port = 8080
    api_key = "your_sabnzbd_api_key"
```
{% endcode %}

## Docker Compose Integration

When using Docker Compose, make sure your download clients are accessible from the MediaManager backend:

{% code title="docker-compose.yml" %}
```yaml
services:
  # MediaManager backend
  backend:
    image: ghcr.io/maxdorninger/mediamanager/backend:latest
    # ... other configuration ...

  # qBittorrent service
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    ports:
      - "8080:8080"
    environment:
      - WEBUI_PORT=8080
    volumes:
      - ./data/torrents:/downloads
    # ... other configuration ...

  # SABnzbd service
  sabnzbd:
    image: lscr.io/linuxserver/sabnzbd:latest
    ports:
      - "8081:8080"
    volumes:
      - ./data/usenet:/downloads
    # ... other configuration ...
```
{% endcode %}

{% hint style="warning" %}
You should enable only one BitTorrent and only one Usenet Download Client at any time.
{% endhint %}

{% hint style="info" %}
Make sure the download directories in your download clients are accessible to MediaManager for proper file management and organization.
{% endhint %}
