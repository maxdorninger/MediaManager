# URL Prefix

MediaManager, by default, expects to run at the base of a domain, e.g. `maxdorninger.github.io`.

In order to run it on a prefixed path, like `maxdorninger.github.io/media`, the docker image must be built with a special build argument. That's because SvelteKit needs to know the base URL at build time.

In short, clone the repository, then run:

```none title="Build Docker image"
docker build \
  --build-arg BASE_PATH=/media \
  --build-arg VERSION=my-custom-version \
  -t MediaManager:my-custom-version \
  -f Dockerfile .
```

You also need to set the `BASE_PATH` environment variable at runtime in `docker-compose.yaml`:

* `BASE_PATH`\
  Base path prefix MediaManager is served under. Example: `/media`. This must match the `BASE_PATH` build arg.

```yaml title="docker-compose.yaml (excerpt)"
services:
  mediamanager:
    image: MediaManager:my-custom-version
    ports:
      - "8000:8000"
    environment:
      BASE_PATH: /media
      ...
```

!!! info
    Make sure to include the base path in the `frontend_url` field in the config file. See [Backend](../configuration/backend.md).

Finally, ensure that whatever reverse proxy you're using leaves the incoming path unchanged; that is, you should not strip the `/media` from `/media/web/`.
