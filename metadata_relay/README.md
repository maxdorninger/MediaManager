# MetadataRelay

This is a service that provides metadata for movies and TV shows. It is advisable to use a load balancer/CDN like
Cloudflare to cache requests as to not overload the TMDB/TVDB api. I (the developer) run a
public instance of this service at https://metadata-relay.dorninger.co, but you can also run your
own instance.

## Example Docker Compose Configuration

````yaml
services:
  metadata_relay:
    image: ghcr.io/maxdorninger/mediamanager/metadata_relay:latest
    restart: always
    environment:
      - TMDB_API_KEY=  # you need not provide a TMDB API key, if you only want to use TVDB metadata, or the other way around
      - TVDB_API_KEY=
    container_name: metadata_relay
    ports:
      - 8000:8000
````