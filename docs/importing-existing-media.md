# Importing existing media

In order for MediaManager to be able to import existing media (e.g. downloaded by Sonarr or Radarr) two conditions have to be met:

* The folder's name must not start with a dot.
* The media must be in the root tv/movie library.

Here is an example, using these rules:

```
/
└── data/
    ├── tv/
    │   ├── Rick and Morty                          # WILL be imported
    │   ├── Stranger Things (2016) {tvdb_12345} [x265]  # WILL be imported
    │   ├── Breaking Bad (2008) [tmdbid-1396]      # WILL be imported
    │   ├── .The Office (2013)                     # WILL NOT
    │   └── my-custom-library/
    │       └── The Simpsons                       # WILL NOT be imported
    └── movie/
        └── Oppenheimer (2023)                    # WILL be imported
```

If your folder structure is in the correct format, you can start importing. To do this, log in as an administrator and go to the TV/movie dashboard.

!!! info
    After importing, MediaManager will automatically prefix the old root TV show/movie folders with a dot to mark them as "imported".

So after importing, the directory would look like this (using the above directory structure):

```
/
└── data/
    ├── tv/
    │   ├── .Rick and Morty                          # RENAMED
    │   ├── Rick and Morty (2013) [tmdbid-60625]     # IMPORTED
    │   ├── .Stranger Things (2016) {tvdb_12345}    # RENAMED
    │   ├── Stranger Things (2016) [tmdbid-66732]    # IMPORTED
    │   ├── .The Office (2013)                       # IGNORED
    │   ├── .Breaking Bad (2008) [tmdbid-1396]       # RENAMED
    │   ├── Breaking Bad (2008) [tmdbid-1396]        # IMPORTED
    │   └── my-custom-library/
    │       └── The Simpsons                         # IGNORED
    └── movie/
        ├── .Oppenheimer (2023)                      # RENAMED
        └── Oppenheimer (2023) [tmdbid-872585]       # IMPORTED
```

## More criteria for importing

These are the criteria specifically for the files themselves:

* Movie folders (e.g. `Oppenheimer (2023)`) must contain exactly one video file (e.g. .mp4, .mkv).
* The specific structure of season folders or episode folders or naming of them does not matter.
* Episode files (video and subtitle files) must contain the season and episode number in their name, e.g. `S01E01.mp4` or `S03E07 Rick and Morty.mkv`.

## Miscellaneous information

* Make MediaManager ignore directories by prefixing them with a dot.
* After importing, especially TV shows, manually check if all files are in the right place.
* MediaManager outputs in the logs if an episode/movie could not be imported.

Last updated: 20 December 2025
