# Indexers

Indexer settings are configured in the `[indexers]` section of your `config.toml` file. MediaManager supports both
Prowlarr and Jackett as indexer providers.

## Prowlarr (`[indexers.prowlarr]`)

- `enabled`

Set to `true` to enable Prowlarr. Default is `false`.

- `url`

Base URL of your Prowlarr instance.

- `api_key`

API key for Prowlarr. You can find this in Prowlarr's settings under General.

- `reject_torrents_on_url_error`

Set to `true` to reject torrents if there is a URL error when fetching from Prowlarr. Until MediaManager v1.9.0 the
default behavior was `false`, but from v1.9.0 onwards the default is `true`. It's recommended to set this to `true` to
avoid adding possibly invalid torrents. 

## Jackett (`[indexers.jackett]`)

- `enabled`

Set to `true` to enable Jackett. Default is `false`.

- `url`

Base URL of your Jackett instance.

- `api_key`

API key for Jackett. You can find this in Jackett's dashboard.

- `indexers`

List of indexer names to use with Jackett. You can specify which indexers Jackett should search through.

## Example Configuration

Here's a complete example of the indexers section in your `config.toml`:

```toml
[indexers]
[indexers.prowlarr]
enabled = true
url = "http://prowlarr:9696"
api_key = "your_prowlarr_api_key"

[indexers.jackett]
enabled = false
url = "http://jackett:9117"
api_key = "your_jackett_api_key"
indexers = ["1337x", "rarbg"]
```
