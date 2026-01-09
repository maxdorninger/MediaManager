# Logging

MediaManager automatically logs events and errors to help with troubleshooting and monitoring. These logs are emitted to the console (stdout) by default, and to a json-formatted log file.

## Configuring Logging

The following are configured as environment variables.

* `LOG_FILE`\
  Path to the JSON log file. Default is `/app/config/media_manager.log`. The directory must exist and be writable.
* `MEDIAMANAGER_LOG_LEVEL`\
  Logging level. Default is `INFO`. Supported values: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
