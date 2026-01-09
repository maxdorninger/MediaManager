# Troubleshooting

{% hint style="info" %}
Always check the container and browser logs for more specific error messages
{% endhint %}

<details>

<summary>Authentication Issues</summary>

#### I can't log in with OAuth/OIDC?

Verify provider configurationVerify your OAuth provider's configuration. See the OAuth documentationCheck callback URICheck if the callback URI you set in your OIDC providers settings is correct. See the callback URI documentationCheck frontend URLCheck the frontend url in your config file. It should match the URL you use to access MediaManager.

</details>

<details>

<summary>I cannot log in?</summary>

Confirm login vs signupMake sure you are logging in, not signing up.Try default credentialsTry logging in with the following credentials:Email: admin@mediamanager.local or admin@example.comPassword: admin

</details>

<details>

<summary>Hard linking Issues</summary>

* Make sure you are using only one volumes for TV, Movies and Downloads. [See the configuration in the example `docker-compose.yaml` file.](https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/docker-compose.yaml)

The reason is that hard linking only works within the same filesystem. If your downloads are on a different volume than your media library, hard linking will not work.

</details>

<details>

<summary>Torrent Search Issues</summary>

#### I get no search results for torrents?

Switch to advanced tabTry switching to the advanced tab when searching for torrents.Increase timeout for slow indexersIf you use "slow" indexers, try increasing the timeout threshold.Check logsIf you still don't get any search results, check the logs, they will provide more information on what is going wrong.

</details>

<details>

<summary>Import and download Issues</summary>

* If you configured a category with a special save path, [carefully read this page about MM with qBittorrent save paths.](advanced-features/qbittorrent-category.md)

</details>

<details>

<summary>Docker Image Pull Issues</summary>

* If you get a 401 or 403 error when pulling the image from GHCR, this is not a permission issue with the repository/image. It errors because your Docker client is misconfigured.
* This is not a MediaManager issue per se, so please don't open an issue about this on the MediaManager GitHub repo.

#### Possible Fixes:

* [Unable to pull image from GitHub Container Registry (Stack Overflow)](https://stackoverflow.com/questions/74656167/unable-to-pull-image-from-github-container-registry-ghcr)
* [Try pulling the image from Quay.io](/broken/pages/09241b2fcda5d337e8878e4052f4634fe2902d10#mediamanager-and-metadatarelay-docker-images)

</details>

{% hint style="info" %}
If it still doesn't work, [please open an Issue.](https://github.com/maxdorninger/MediaManager/issues) It is possible that a bug is causing the issue.
{% endhint %}
