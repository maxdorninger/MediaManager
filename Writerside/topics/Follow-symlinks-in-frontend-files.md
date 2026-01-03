# Follow symlinks in frontend files

MediaManager can be configured to follow symlinks when serving frontend files. This is useful if you have a setup where
your frontend files are stored in a different location, and you want to symlink them into the MediaManager frontend directory.

To enable this feature, set the `FRONTEND_FOLLOW_SYMLINKS` environment variable to `true`.
