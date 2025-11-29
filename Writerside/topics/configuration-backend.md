# Backend

These settings configure the core backend application through the `config.toml` file. All backend configuration is now
centralized in this TOML file instead of environment variables.

## General Settings (`[misc]`)

- `frontend_url`

The URL the frontend will be accessed from. This is a required field and must not include a trailing slash. The default
path is `http://localhost:8000`.

E.g. if you are accessing MediaManager at `http://example.com/media` where `/media` is the base path, set this to: `http://example.com/media`.

If you are accessing MediaManager at the root of a domain, e.g. `https://mediamanager.example.com`, set this to `https://mediamanager.example.com`.

Make sure to change this to the URL you will use to access the application in your browser.

<tip>
    Note that this doesn't affect where the server binds, nor does it affect the base URL prefix. See the page on <a href="url-prefix.md"><code>BASE_PATH</code></a> for information on how to configure a prefix.
</tip>

- `cors_urls`

A list of origins you are going to access the API from. Note the lack of trailing slashes.

- `development`

Set to `true` to enable development mode. Default is `false`.

## Example Configuration

Here's a complete example of the general settings section in your `config.toml`:

```toml
[misc]
# REQUIRED: Change this to match your actual frontend domain.
frontend_url = "http://mediamanager.dev"

cors_urls = ["http://localhost:8000"]

# Optional: Development mode (set to true for debugging)
development = false
```

<note>
    The <code>frontend_url</code> is the most important settings to configure correctly. Make sure it matches your actual deployment URLs.
</note>
