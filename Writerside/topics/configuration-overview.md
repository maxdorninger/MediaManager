# Installation Guide

The recommended way to install and run Media Manager is using Docker and Docker Compose.

## Prerequisites

* Ensure Docker and Docker Compose are installed on your system.
* If you plan to use OAuth 2.0 / OpenID Connect for authentication, you will need an account and client credentials
  from an OpenID provider (e.g., Authentik, Pocket ID).

## Setup

* Download the `docker-compose.yaml` from the MediaManager repo with the following command:
  ```bash
  wget -O docker-compose.yaml https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/docker-compose.yaml
  mkdir config
  wget -O ./config/config.toml https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/config.example.toml
  # you probably need to edit the config.toml file in the ./config directory, for more help see the documentation
  docker compose up -d
  ```

* Upon first run, MediaManager will create a default `config.toml` file in the `./config` directory.

* You can edit this file to configure MediaManager according to your needs.

* Upon first run, MediaManager will also create a default admin user with the email, it's recommended to change the
  password of this user after the first login. The credentials of the default admin user will be printed in the logs of
  the container.

* For more information on the available configuration options, see the [Configuration section](Configuration.md) of the
  documentation.

<include from="notes.topic" element-id="auth-admin-emails"></include>

## MediaManager and MetadataRelay Docker Images

MediaManager is available as a Docker image on both Red Hat Quay.io and GitHub Container Registry (GHCR):

- `quay.io/maxdorninger/mediamanager`
- `ghcr.io/maxdorninger/mediamanager/mediamanager`

MetadataRelay Images are also available on both registries:

- `quay.io/maxdorninger/metadata_relay`
- `ghcr.io/maxdorninger/mediamanager/metadata_relay`

From v1.12.1 onwards, both MediaManager and MetadataRelay images are available on both Quay.io and GHCR.
The reason for the switch to Quay.io as the primary image registry is due
to [GHCR's continued slow performance](https://github.com/orgs/community/discussions/173607).

<note>
    You can use either the Quay.io or GHCR images interchangeably,
    as they are built from the same source and the tags are the same across both registries.
</note>

### Tags

Both registries support the following tags:
- `latest`: Points to the latest stable release.
- `master`: Points to the latest commit on the master branch (may be unstable).
- `X.Y.Z`: Specific version tags (e.g., `1.12.0`).
- `X.Y`: Points to the latest release in the X.Y series (e.g., `1.12`).
- `X`: Points to the latest release in the X series (e.g., `1`).
- `pr-<number>`: Points to the latest commit in the specified pull request (e.g., `pr-67`).
