# Backend

These settings configure the core backend application through the `config.toml` file. All backend configuration is now
centralized in this TOML file instead of environment variables.

## General Settings (`[misc]`)

- `frontend_url`

The URL the frontend will be accessed from. This is a required field and must include the trailing slash. The default
path is `http://localhost:8000/web/`.

Make sure to change this to the URL you will use to access the application in your browser.

Note that this doesn't affect where the server binds, nor does it affect the base URL prefix. See the page on <a href="url-prefix.md"`>`BASE_PATH`</a> for information on how to configure a prefix.

- `cors_urls`

A list of origins you are going to access the API from. Note the lack of trailing slashes.

- `development`

Set to `true` to enable development mode. Default is `false`.

## Example Configuration

Here's a complete example of the general settings section in your `config.toml`:

```toml
[misc]
# REQUIRED: Change this to match your actual frontend domain.
frontend_url = "http://mediamanager.dev/"

cors_urls = ["http://localhost:8000"]

# Optional: Development mode (set to true for debugging)
development = false
```

<note>
    The <code>frontend_url</code> is the most important settings to configure correctly. Make sure it matches your actual deployment URLs.
</note>
