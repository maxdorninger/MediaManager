# Logging

MediaManager automatically logs events and errors to help with troubleshooting and monitoring. These logs are emitted to
the console (stdout) by default, and to a json-formatted log file.

## Configuring Logging

The location of the log file can be configured with the `LOG_FILE` environment variable. By default, the log file is
located at
`/app/config/media_manager.log`. When changing the log file location, ensure that the directory exists, is writable by the
MediaManager container and that it is a full path.

With the `MEDIAMANAGER_LOG_LEVEL` environment variable, you can set the logging level. The available levels are:
- `DEBUG` - Detailed information, typically of interest only when diagnosing problems.
- `INFO` - The default level, for general operational entries about what's going on inside the application.
- `WARNING`
- `ERROR`