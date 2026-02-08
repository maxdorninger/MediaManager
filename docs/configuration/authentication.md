---
description: >-
  MediaManager supports multiple authentication methods. Email/password
  authentication is the default, but you can also enable OpenID Connect (OAuth
  2.0) for integration with external identity providers
---

# Authentication

All authentication settings are configured in the `[auth]` section of your `config.toml` file.

## General Authentication Settings (`[auth]`)

* `token_secret`\
  Strong secret key for signing JWTs (create with `openssl rand -hex 32`). This is required.
* `session_lifetime`\
  Lifetime of user sessions in seconds. Default is `86400` (1 day).
* `admin_emails`\
  A list of email addresses for administrator accounts. This is required.
* `email_password_resets`\
  Enables password resets via email. Default is `false`.

!!! info
    To use email password resets, you must also configure SMTP settings in the `[notifications.smtp_config]` section.

!!! info
    When setting up MediaManager for the first time, you should add your email to `admin_emails` in the `[auth]` config section. MediaManager will then use this email instead of the default admin email. Your account will automatically be created as an admin account, allowing you to manage other users, media and settings.

## OpenID Connect Settings (`[auth.openid_connect]`)

OpenID Connect allows you to integrate with external identity providers like Google, Microsoft Azure AD, Keycloak, or any other OIDC-compliant provider.

* `enabled`\
  Set to `true` to enable OpenID Connect authentication. Default is `false`.
* `client_id`\
  Client ID provided by your OpenID Connect provider.
* `client_secret`\
  Client secret provided by your OpenID Connect provider.
* `configuration_endpoint`\
  OpenID Connect configuration endpoint URL. Do not include a trailing slash. Usually ends with `/.well-known/openid-configuration`.
* `name`\
  Display name for the OpenID Connect provider shown on the login page.

### Configuration for your OpenID Connect Provider

#### Redirect URI

The OpenID server will likely require a redirect URI. This URL will usually look something like this:

```none
{MEDIAMANAGER_URL}/api/v1/auth/oauth/callback
```

!!! warning
    It is very important that you set the correct callback URI, otherwise it won't work!

#### Authentik Example

Here is an example configuration for the OpenID Connect provider for Authentik.

![authentik-redirect-url-example](<../assets/assets/authentik redirect url example.png>)

## Example Configuration

Here's a complete example of the authentication section in your `config.toml`:

```toml title="config.toml"
[auth]
token_secret = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
session_lifetime = 604800  # 1 week
admin_emails = ["admin@example.com", "manager@example.com"]
email_password_resets = true

[auth.openid_connect]
enabled = true
client_id = "mediamanager-client"
client_secret = "your-secret-key-here"
configuration_endpoint = "https://auth.example.com/.well-known/openid-configuration"
name = "Authentik"
```

