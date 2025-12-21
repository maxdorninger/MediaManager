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

### `primary_languages`

If a TV show/movie's original language is in this list, metadata will be displayed and fetched in that language. Torrent searches done in Standard Mode uses the same fetched metadata, so if you use any language-specific tracker, you may enter the language here to get the desired search results.
Otherwise, `default_language` will be used.

**Format: ISO 639-1 codes (2 letters). Full list: https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes**

- **Default:** `[]`
- **Example:** `["no", "de", "es"]`

### `default_language`

<warning>
    `default_language` sets the TMDB `language` paramater when searching and adding TV shows and movies. If TMDB does not find a matching translation, metadata in the <strong>original language</strong> will be fetched with no option for a fallback language. It is therefore highly advised to only use "broad" languages. For most use cases, the default setting is safest.
</warning>

**Format: ISO 639-1 codes (2 letters).**

- **Default:** `en`

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
