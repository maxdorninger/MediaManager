# Metadata Provider Configuration

Metadata provider settings are configured in the `[metadata]` section of your `config.toml` file. These settings control how MediaManager retrieves information about movies and TV shows.

## TMDB Settings (`[metadata.tmdb]`)

TMDB (The Movie Database) is the primary metadata provider for MediaManager. It provides detailed information about movies and TV shows.

<tip>
    Other software like Jellyfin use TMDB as well, so there won't be any metadata discrepancies.
</tip>

### `tmdb_relay_url`

If you want to use your own TMDB relay service, set this to the URL of your own MetadataRelay. Otherwise, use the default relay.

- **Default:** `https://metadata-relay.dorninger.co/tmdb`
- **Example:** `https://your-own-relay.example.com/tmdb`

## TVDB Settings (`[metadata.tvdb]`)

<warning>
    The TVDB might provide false metadata and doesn't support some features of MediaManager like showing overviews. Therefore, TMDB is the preferred metadata provider.
</warning>

### `tvdb_relay_url`

If you want to use your own TVDB relay service, set this to the URL of your own MetadataRelay. Otherwise, use the default relay.

- **Default:** `https://metadata-relay.dorninger.co/tvdb`
- **Example:** `https://your-own-relay.example.com/tvdb`

## MetadataRelay

<note>
  To use MediaManager <strong>you don't need to set up your own MetadataRelay</strong>, as the default relay hosted by the developer should be sufficient for most purposes.
</note>

The MetadataRelay is a service that provides metadata for MediaManager. It acts as a proxy for TMDB and TVDB, allowing you to use your own API keys if needed, but the default relay means you don't need to create accounts for API keys yourself.

You might want to use your own relay if you want to avoid rate limits, protect your privacy, or for other reasons. If you know Sonarr's Skyhook, this is similar to that.

### Where to get API keys

- Get a TMDB API key from [The Movie Database](https://www.themoviedb.org/settings/api)
- Get a TVDB API key from [The TVDB](https://thetvdb.com/auth/register)

<tip>
    If you want to use your own MetadataRelay, you can set the <code>tmdb_relay_url</code> and/or <code>tvdb_relay_url</code> to your own relay service.
</tip>

## Example Configuration

Here's a complete example of the metadata section in your `config.toml`:

```toml
[metadata]
    # TMDB configuration
    [metadata.tmdb]
    tmdb_relay_url = "https://metadata-relay.dorninger.co/tmdb"

    # TVDB configuration  
    [metadata.tvdb]
    tvdb_relay_url = "https://metadata-relay.dorninger.co/tvdb"
```

<note>
    In most cases, you can simply use the default values and don't need to specify these settings in your config file at all.
</note>
