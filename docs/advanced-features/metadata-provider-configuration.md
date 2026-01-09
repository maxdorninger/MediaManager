# Metadata Provider Configuration

## Metadata Provider Configuration

Metadata provider settings are configured in the `[metadata]` section of your `config.toml` file. These settings control how MediaManager retrieves information about movies and TV shows.

### TMDB Settings (`[metadata.tmdb]`)

TMDB (The Movie Database) is the primary metadata provider for MediaManager. It provides detailed information about movies and TV shows.

{% hint style="info" %}
Other software like Jellyfin use TMDB as well, so there won't be any metadata discrepancies.
{% endhint %}

* `tmdb_relay_url`\
  URL of the TMDB relay (MetadataRelay). Default is `https://metadata-relay.dorninger.co/tmdb`. Example: `https://your-own-relay.example.com/tmdb`.
* `primary_languages`\
  If the original language of a show/movie is in this list, metadata is fetched in that language. Otherwise, `default_language` is used. Default is `[]`. Example: `["no", "de", "es"]`. Format: ISO 639-1 (2 letters). Full list: https://en.wikipedia.org/wiki/List\_of\_ISO\_639\_language\_codes
* `default_language`\
  TMDB language parameter used when searching and adding. Default is `en`. Format: ISO 639-1 (2 letters).

{% hint style="warning" %}
`default_language` sets the TMDB `language` parameter when searching and adding TV shows and movies. If TMDB does not find a matching translation, metadata in the original language will be fetched with no option for a fallback language. It is therefore highly advised to only use "broad" languages. For most use cases, the default setting is safest.
{% endhint %}

### TVDB Settings (`[metadata.tvdb]`)

{% hint style="warning" %}
The TVDB might provide false metadata and doesn't support some features of MediaManager like showing overviews. Therefore, TMDB is the preferred metadata provider.
{% endhint %}

* `tvdb_relay_url`\
  URL of the TVDB relay (MetadataRelay). Default is `https://metadata-relay.dorninger.co/tvdb`. Example: `https://your-own-relay.example.com/tvdb`.

### MetadataRelay

{% hint style="info" %}
To use MediaManager you don't need to set up your own MetadataRelay, as the default relay hosted by the developer should be sufficient for most purposes.
{% endhint %}

The MetadataRelay is a service that provides metadata for MediaManager. It acts as a proxy for TMDB and TVDB, allowing you to use your own API keys if needed, but the default relay means you don't need to create accounts for API keys yourself.

You might want to use your own relay if you want to avoid rate limits, protect your privacy, or for other reasons. If you know Sonarr's Skyhook, this is similar to that.

#### Where to get API keys

* Get a TMDB API key from [The Movie Database](https://www.themoviedb.org/settings/api)
* Get a TVDB API key from [The TVDB](https://thetvdb.com/auth/register)

{% hint style="info" %}
If you want to use your own MetadataRelay, you can set the `tmdb_relay_url` and/or `tvdb_relay_url` to your own relay service.
{% endhint %}

### Example Configuration

Here's a complete example of the metadata section in your `config.toml`:

{% code title="config.toml" %}
```toml
[metadata]
    # TMDB configuration
    [metadata.tmdb]
    tmdb_relay_url = "https://metadata-relay.dorninger.co/tmdb"

    # TVDB configuration
    [metadata.tvdb]
    tvdb_relay_url = "https://metadata-relay.dorninger.co/tvdb"
```
{% endcode %}

{% hint style="info" %}
In most cases, you can simply use the default values and don't need to specify these settings in your config file at all.
{% endhint %}
