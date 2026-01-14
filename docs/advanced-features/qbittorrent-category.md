# qBittorrent Category

qBittorrent supports saving Torrents to subdirectories based on the category of the Torrent. The default category name that MediaManager uses is `MediaManager`.

Use the following variables to customize behavior:

* `torrents.qbittorrent.category_name`\
  Category name MediaManager uses when adding torrents to qBittorrent. Default is `MediaManager`.
* `torrents.qbittorrent.category_save_path`\
  Save path for the category in qBittorrent. By default, no subdirectory is used. Example: `/data/torrents/MediaManager`.

{% hint style="info" %}
qBittorrent saves torrents to the path specified by `torrents.qbittorrent.category_save_path`, so it must be a valid path that qBittorrent can write to.
{% endhint %}

{% hint style="warning" %}
For MediaManager to successfully import torrents, you must add the subdirectory to the `misc.torrent_directory` variable.
{% endhint %}
