# Follow symlinks in frontend files

MediaManager can be configured to follow symlinks when serving frontend files. This is useful if you have a setup where your frontend files are stored in a different location, and you want to symlink them into the MediaManager frontend directory.



* `FRONTEND_FOLLOW_SYMLINKS`\
  Set this environment variable to `true` to follow symlinks when serving frontend files. Default is `false`.

```bash title=".env"
FRONTEND_FOLLOW_SYMLINKS=true
```
