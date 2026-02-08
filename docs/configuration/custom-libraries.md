# Custom Libraries

MediaManager supports custom libraries, allowing you to add multiple folders for your movies and TV series. This feature is useful if you organize your media into different directories. For example, you might have separate folders for "Action" movies and "Comedy" movies, or "Live Action" TV shows and "Animated" TV shows.

## Configuration

Custom libraries are configured in the `misc` section in the `config.toml` file. You can add as many libraries as you need.

!!! info
    You are not limited to `/data/tv` or `/data/movies`, you can choose the entire path freely!

### Movie Libraries

To add custom movie libraries, add a `[[misc.movie_libraries]]` section for each library. Each library requires a `name` and a `path`.

Example — configuring two movie libraries:

```toml
[misc]

# ... other misc settings

[[misc.movie_libraries]]
name = "Action"
path = "/data/movies/action"

[[misc.movie_libraries]]
name = "Comedy"
path = "/data/movies/comedy"
```

In this example, MediaManager will scan both `/data/movies/action` and `/data/movies/comedy` for movies.

### TV Show Libraries

Similarly, to add custom TV show libraries, add a `[[misc.tv_libraries]]` section for each library. Each library requires a `name` and a `path`.

Example — configuring two TV show libraries:

```toml
[misc]

# ... other misc settings

[[misc.tv_libraries]]
name = "Live Action"
path = "/data/tv/live-action"

[[misc.tv_libraries]]
name = "Animation"
path = "/data/tv/animation"
```
