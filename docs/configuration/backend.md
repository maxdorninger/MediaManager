---
description: >-
  These settings configure the core backend application through the config.toml
  file. All backend configuration is now centralized in this TOML file instead
  of environment variables.
---

# Backend

## General Settings (`[misc]`)

*   `frontend_url`\
    The URL the frontend will be accessed from. This is required. Do not include a trailing slash. Default is `http://localhost:8000`.

    Example: if you are accessing MediaManager at `http://example.com/media`, set this to `http://example.com/media`.

    If you are accessing MediaManager at the root of a domain, e.g. `https://mediamanager.example.com`, set this to `https://mediamanager.example.com`.

    `frontend_url` does not affect where the server binds. It also does not configure a base path prefix. For prefixes, see [URL Prefix](../advanced-features/url-prefix.md).
* `cors_urls`\
  A list of origins you are going to access the API from. Do not include trailing slashes.
* `development`\
  Set to `true` to enable development mode. Default is `false`.

## Example Configuration

Here's a complete example of the general settings section in your `config.toml`:

{% code title="config.toml" %}
```toml
[misc]

# REQUIRED: Change this to match your actual frontend domain.
frontend_url = "http://mediamanager.dev"

cors_urls = ["http://localhost:8000"]

# Optional: Development mode (set to true for debugging)
development = false
```
{% endcode %}

{% hint style="info" %}
The `frontend_url` is the most important setting to configure correctly. Make sure it matches your actual deployment URLs.
{% endhint %}
