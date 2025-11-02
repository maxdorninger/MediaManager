# Logging

MediaManager automatically logs events and errors to help with troubleshooting and monitoring. These logs are emitted to
the console (stdout) by default, and to a json-formatted log file.

## Configuring Logging

The location of the log file can be configured with the `LOG_FILE` environment variable. By default, the log file is
located at
`/app/config/media_manager.log`. When changing the log file location, ensure that the directory exists, is writable by the
MediaManager container and that it is a full path.