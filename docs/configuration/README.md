# Configuration

MediaManager uses a TOML configuration file (`config.toml`) for all backend settings. This centralized configuration approach makes it easier to manage, backup, and share your MediaManager setup.

Frontend settings are configured through environment variables in your `docker-compose.yaml` file.

## Configuration File Location

!!! warning
    Note that MediaManager may need to be restarted for changes in the config file to take effect.

Your `config.toml` file should be in the directory that's mounted to `/app/config/config.toml` inside the container:

```yaml
volumes:
  - ./config:/app/config
```

You can change the configuration directory with the following environment variable:

* `CONFIG_DIR`\
  Directory that contains `config.toml`. Default is `/app/config`. Example: `/etc/mediamanager/`.

## Configuration Sections

The configuration is organized into the following sections:

* `[misc]` - General settings
* `[database]` - Database settings
* `[auth]` - Authentication settings
* `[notifications]` - Notification settings (Email, Gotify, Ntfy, Pushover)
* `[torrents]` - Download client settings (qBittorrent, Transmission, SABnzbd)
* `[indexers]` - Indexer settings (Prowlarr and Jackett )
* `[metadata]` - TMDB and TVDB settings

## Configuring Secrets

For sensitive information like API keys, passwords, and secrets, you should use environment variables. You can actually set every configuration value through environment variables. For example, to set the `token_secret` value for authentication, with a .toml file you would use:

```toml
[auth]
token_secret = "your_super_secret_key_here"
```

But you can also set it through an environment variable:

```none
MEDIAMANAGER_AUTH__TOKEN_SECRET = "your_super_secret_key_here"
```

or another example with the OIDC client secret:

```toml
[auth]
...
[auth.openid_connect]
client_secret = "your_client_secret_from_provider"
```

env variable:

```none
MEDIAMANAGER_AUTH__OPENID_CONNECT__CLIENT_SECRET = "your_client_secret_from_provider"
```

So for every config "level", you basically have to take the name of the value and prepend it with the section names in uppercase with 2 underscores as delimiters and `MEDIAMANAGER_` as the prefix.

!!! warning
    Note that not every env variable starts with `MEDIAMANAGER_`; this prefix only applies to env variables which replace/overwrite values in the config file. Variables like the `CONFIG_DIR` env variable must not be prefixed.
