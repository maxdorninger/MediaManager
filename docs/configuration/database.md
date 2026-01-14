# Database

Database settings are configured in the `[database]` section of your `config.toml` file. MediaManager uses PostgreSQL as its database backend.

## Database Settings (`[database]`)

* `host`\
  Hostname or IP of the PostgreSQL server. Default is `localhost`.
* `port`\
  Port number of the PostgreSQL server. Default is `5432`.
* `user`\
  Username for the PostgreSQL connection. Default is `MediaManager`.
* `password`\
  Password for the PostgreSQL user. Default is `MediaManager`.
* `dbname`\
  Name of the PostgreSQL database. Default is `MediaManager`.

## Example Configuration

Here's a complete example of the database section in your `config.toml`:

{% code title="config.toml" %}
```toml
[database]
host = "db"
port = 5432
user = "MediaManager"
password = "your_secure_password"
dbname = "MediaManager"
```
{% endcode %}

{% hint style="info" %}
In docker-compose deployments the container name is simultaneously its hostname, so you can use "db" or "postgres" as host.
{% endhint %}
