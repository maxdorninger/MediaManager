# Importing existing media

In order for MediaManager to be able to import existing media (e.g. downloaded by Sonarr or Radarr)
3 conditions have to be met:

1. The folder's name must not contain `[tmdbid-xxxxx]` or `[tvdbid-xxxxx]`.
2. The folder's name must not start with a dot.
3. The media must be in the root tv/movie library

Here is an example, using these rules:

```
/
└── data/
    ├── tv/
    │   ├── Rick and Morty # WILL be imorted
    │   ├── Stranger Things (2016) # WILL be imported
    │   │
    │   ├── Breaking Bad (2008) [tmdbid-1396] # WILL NOT be imported
    │   ├── .The Office (2013) # WILL NOT
    │   │
    │   └── my-custom-library/
    │       └── The Simpsons # WILL NOT be imported
    └── movie/
        └── Oppenheimer (2023) # WILL be imported
```

Is your folder structure in the correct format, you can start importing. For this,
you just need to login as an administrator and go to the TV/movie dashboard.

<note>
When importing, no files will be deleted, moved or copied! Instead, they will be hard linked.
</note>

After importing, MediaManager will automatically prefix the old root TV show/movie folders with a dot,
in order to mark them as 'imported'.

So after importing, the directory would look like this (using the above directory structure):

```
/
└── data/
    ├── tv/
    │   ├── .Rick and Morty # RENAMED
    │   ├── Rick and Morty (2013) [tmdbid-60625] # IMPORTED
    │   │
    │   ├── .Stranger Things (2016) # RENAMED
    │   ├── Stranger Things (2016) [tmdbid-66732] # IMPORTED
    │   │
    │   ├── .The Office (2013) # IGNORED
    │   ├── Breaking Bad (2008) [tmdbid-1396] # IGNORED
    │   │
    │   └── my-custom-library/
    │       └── The Simpsons # IGNORED
    └── movie/
        ├── .Oppenheimer (2023) # RENAMED
        └── Oppenheimer (2023) [tmdbid-872585] # IMPORTED
```

## More criteria for importing

These are the criteria specifically for the files themselves:

- movie folders (e.g. `Oppenheimer (2023)`) must not contain more or less than one video file (an .mp4 or .mkv, etc.
  file)
- the specific structure of season folders or episode folders or naming of them does not matter
- Episode files (video and subtitle files) must contain the season and episode number in their name, e.g. `S01E01.mp4`
  or `S03E07 Rick and Morty.mkv`

<tip>
In any usual Sonarr/Radarr setup these file criteria should already be met by default.
</tip>

## Miscellaneous information

- make MediaManager ignore directories by prefixing them with a dot
- after importing, especially TV shows, manually check if all files are in the right place
- MediaManager outputs in the logs if an episode/movie could not be imported
