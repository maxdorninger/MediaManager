# Download Clients

Download client settings are configured in the `[torrents]` section of your `config.toml` file. MediaManager supports qBittorrent and Transmission as torrent clients, and SABnzbd and NZBGet as usenet clients.

## qBittorrent Settings (`[torrents.qbittorrent]`)

qBittorrent is a popular BitTorrent client that MediaManager can integrate with for downloading torrents.

- `enabled`

Set to `true` to enable qBittorrent integration. Default is `false`.

- `host`

Hostname or IP of the qBittorrent server. Include the protocol (http/https).

- `port`

Port of the qBittorrent Web UI/API. Default is `8080`.

- `username`

Username for qBittorrent Web UI authentication. Default is `admin`.

- `password`

Password for qBittorrent Web UI authentication. Default is `admin`.

## Transmission Settings (`[torrents.transmission]`)

<note>

The downloads path in Transmission and MediaManager __must__ be the same, i.e. the path `/data/torrents` must link to the same volume for both containers.

</note>

Transmission is a BitTorrent client that MediaManager can integrate with for downloading torrents.

- `enabled`

Set to `true` to enable Transmission integration. Default is `false`.

- `username`

Username for Transmission RPC authentication.

- `password`

Password for Transmission RPC authentication.

- `https_enabled`

Set to `true` if your Transmission RPC endpoint uses HTTPS. Default is `true`.

- `host`

Hostname or IP of the Transmission server (without protocol).

- `port`

Port of the Transmission RPC endpoint. Default is `9091`.

- `path`

RPC request path target. Usually `/transmission/rpc`.

## SABnzbd Settings (`[torrents.sabnzbd]`)

SABnzbd is a Usenet newsreader that MediaManager can integrate with for downloading NZB files.

- `enabled`

Set to `true` to enable SABnzbd integration. Default is `false`.

- `host`

Hostname or IP of the SABnzbd server, it needs to include `http(s)://`.

- `port`

Port of the SABnzbd API. Default is `8080`.

- `api_key`

API key for SABnzbd. You can find this in SABnzbd's configuration under "General" → "API Key".

- `base_path`

API base path for SABnzbd. It usually ends with `/api`, the default is `/api`.

## NZBGet Settings (`[torrents.nzbget]`)

NZBGet is a high-performance Usenet downloader that MediaManager can integrate with for downloading NZB files.

- `enabled`

Set to `true` to enable NZBGet integration. Default is `false`.

- `host`

Hostname or IP of the NZBGet server (without protocol).

- `port`

Port of the NZBGet web interface. Default is `6789`.

- `username`

Username for NZBGet authentication. Default is `nzbget`.

- `password`

Password for NZBGet authentication. Default is `tegbzn6789`.

- `use_https`

Set to `true` if your NZBGet uses HTTPS. Default is `false`.

## Example Configuration

Here's a complete example of the download clients section in your `config.toml`:

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

    # NZBGet configuration
    [torrents.nzbget]
    enabled = false
    host = "nzbget"
    port = 6789
    username = "nzbget"
    password = "your_nzbget_password"
    use_https = false
```

## Docker Compose Integration

When using Docker Compose, make sure your download clients are accessible from the MediaManager backend:

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

  # NZBGet service
  nzbget:
    image: lscr.io/linuxserver/nzbget:latest
    ports:
      - "6789:6789"
    volumes:
      - ./data/usenet:/downloads
    # ... other configuration ...
```

<note>
    You should enable only one BitTorrent and only one Usenet Download Client at any time.
</note>

<tip>
    Make sure the download directories in your download clients are accessible to MediaManager for proper file management and organization.
</tip>
