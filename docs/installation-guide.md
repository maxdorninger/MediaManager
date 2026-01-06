# Installation Guide

The recommended way to install and run Media Manager is using Docker and Docker Compose.

## Prerequisites

* Ensure Docker and Docker Compose are installed on your system.
* If you plan to use OAuth 2.0 / OpenID Connect for authentication, you will need an account and client credentials from an OpenID provider (e.g., Authentik, Pocket ID).

## Setup

Follow these steps to get MediaManager running with Docker Compose:

{% stepper %}
{% step %}
### Get the docker-compose file

Download the `docker-compose.yaml` from the MediaManager repo:

```bash
wget -O docker-compose.yaml https://github.com/maxdorninger/MediaManager/releases/latest/download/docker-compose.yaml
```
{% endstep %}

{% step %}
### Prepare configuration directory and example config

Create a config directory and download the example configuration:

```bash
mkdir config
wget -O ./config/config.toml https://github.com/maxdorninger/MediaManager/releases/latest/download/config.example.toml
```
{% endstep %}

{% step %}
### Edit configuration

You probably need to edit the `config.toml` file in the `./config` directory to suit your environment and preferences. [How to configure MediaManager.](configuration/)
{% endstep %}

{% step %}
### Start MediaManager

Bring up the stack:

```bash
docker compose up -d
```
{% endstep %}
{% endstepper %}

* Upon first run, MediaManager will create a default `config.toml` file in the `./config` directory (if not already present).
* Upon first run, MediaManager will also create a default admin user. The credentials of the default admin user will be printed in the logs of the container — it's recommended to change the password of this user after the first login.
* [For more information on the available configuration options, see the Configuration section of the documentation.](configuration/)

{% hint style="info" %}
When setting up MediaManager for the first time, you should add your email to `admin_emails` in the `[auth]` config section. MediaManager will then use this email instead of the default admin email. Your account will automatically be created as an admin account, allowing you to manage other users, media, and settings.
{% endhint %}

## MediaManager and MetadataRelay Docker Images

MediaManager is available as a Docker image on both Red Hat Quay.io and GitHub Container Registry (GHCR):

* quay.io/maxdorninger/mediamanager
* ghcr.io/maxdorninger/mediamanager/mediamanager

MetadataRelay images are also available on both registries:

* quay.io/maxdorninger/metadata\_relay
* ghcr.io/maxdorninger/mediamanager/metadata\_relay

From v1.12.1 onwards, both MediaManager and MetadataRelay images are available on both Quay.io and GHCR. The reason for the switch to Quay.io as the primary image registry is due to GHCR's continued slow performance: https://github.com/orgs/community/discussions/173607

{% hint style="info" %}
You can use either the Quay.io or GHCR images interchangeably, as they are built from the same source and the tags are the same across both registries.
{% endhint %}

### Tags

Both registries support the following tags:

* latest: Points to the latest stable release.
* master: Points to the latest commit on the master branch (may be unstable).
* X.Y.Z: Specific version tags (e.g., `1.12.0`).
* X.Y: Points to the latest release in the X.Y series (e.g., `1.12`).
* X: Points to the latest release in the X series (e.g., `1`).
* pr-: Points to the latest commit in the specified pull request (e.g., `pr-67`).
