# Notifications

These settings are configured in the `[notifications]` section of your `config.toml` file.

## SMTP Configuration (`[notifications.smtp_config]`)

For sending emails, MediaManager uses the SMTP protocol. You can use any SMTP server, like Gmail or SMTP2GO.

* `smtp_host`\
  Hostname of the SMTP server.
* `smtp_port`\
  Port of the SMTP server.
* `smtp_user`\
  Username for the SMTP server.
* `smtp_password`\
  Password (or app password) for the SMTP server.
* `from_email`\
  From-address used when sending emails.
* `use_tls`\
  Set to `true` to use TLS for the SMTP connection. Default is `true`.

## Email Notifications (`[notifications.email_notifications]`)

Controls which emails receive notifications.

* `enabled`\
  Set to `true` to enable email notifications. Default is `false`.
* `emails`\
  List of email addresses to send notifications to.

## Gotify Notifications (`[notifications.gotify]`)

* `enabled`\
  Set to `true` to enable Gotify notifications. Default is `false`.
* `api_key`\
  API key for Gotify.
* `url`\
  Base URL of your Gotify instance. Do not include a trailing slash.

## Ntfy Notifications (`[notifications.ntfy]`)

* `enabled`\
  Set to `true` to enable Ntfy notifications. Default is `false`.
* `url`\
  URL of your ntfy instance plus the topic.

## Pushover Notifications (`[notifications.pushover]`)

* `enabled`\
  Set to `true` to enable Pushover notifications. Default is `false`.
* `api_key`\
  API key for Pushover.
* `user`\
  User key for Pushover.

## Example Configuration

Here's a complete example of the notifications section in your `config.toml`:

{% code title="config.toml" %}
```toml
[notifications]
    # SMTP settings for email notifications and password resets
    [notifications.smtp_config]
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "your-email@gmail.com"
    smtp_password = "your-app-password"
    from_email = "mediamanager@example.com"
    use_tls = true

    # Email notification settings
    [notifications.email_notifications]
    enabled = true
    emails = ["admin@example.com", "notifications@example.com"]

    # Gotify notification settings
    [notifications.gotify]
    enabled = true
    api_key = "your_gotify_api_key"
    url = "https://gotify.example.com"

    # Ntfy notification settings
    [notifications.ntfy]
    enabled = false
    url = "https://ntfy.sh/your-private-topic"

    # Pushover notification settings
    [notifications.pushover]
    enabled = false
    api_key = "your_pushover_api_key"
    user = "your_pushover_user_key"
```
{% endcode %}

{% hint style="info" %}
You can enable multiple notification methods simultaneously. For example, you could have both email and Gotify notifications enabled at the same time.
{% endhint %}
