<br />
<div align="center">
  <a href="https://maxdorninger.github.io/MediaManager">
    <img src="https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/Writerside/images/logo.svg" alt="Logo" width="260" height="260">
  </a>

<h3 align="center">MediaManager</h3>

  <p align="center">
    Modern management system for your media library
    <br />
    <a href="https://maxdorninger.github.io/MediaManager/introduction.html"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/maxdorninger/MediaManager/issues/new?labels=bug&template=bug_report.md">Report Bug</a>
    &middot;
    <a href="https://github.com/maxdorninger/MediaManager/issues/new?template=feature_request.md">Request Feature</a>
  </p>
</div>


MediaManager is modern software to manage your TV and movie library. It is designed to be a replacement for Sonarr,
Radarr, Overseer, and Jellyseer.
It supports TVDB and TMDB for metadata, supports OIDC and OAuth 2.0 for authentication and supports Prowlarr and
Jackett.
MediaManager is built first and foremost for deployment with Docker, making it easy to set up.

It also provides an API to interact with the software programmatically, allowing for automation and integration with
other services.

## Quick Start

```sh
wget -O docker-compose.yaml https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/docker-compose.yaml   
mkdir config
wget -O ./config/config.toml https://raw.githubusercontent.com/maxdorninger/MediaManager/refs/heads/master/config.example.toml   
# you probably need to edit the config.toml file in the ./config directory, for more help see the documentation
docker compose up -d
```

### [View the docs for installation instructions and more](https://maxdorninger.github.io/MediaManager/configuration-overview.html#configuration-overview)

## Support MediaManager

<a href="https://github.com/sponsors/maxdorninger" target="_blank">
  <img src="https://img.shields.io/badge/Sponsor-Maximilian Dorninger-orange" alt="Sponsor @maxdorninger" />
</a>

<a href="https://buymeacoffee.com/maxdorninger" target="_blank">
  <img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" >
</a>

## Check out the awesome sponsors of MediaManager ❤️

<a href="https://fosstodon.org/@aljazmerzen"><img src="https://github.com/aljazerzen.png" width="80px" alt="Aljaž Mur Eržen" /></a>&nbsp;&nbsp;
<a href="https://github.com/ldrrp"><img src="https://github.com/ldrrp.png" width="80px" alt="Luis Rodriguez" /></a>&nbsp;&nbsp;
<a href="https://github.com/brandon-dacrib"><img src="https://github.com/brandon-dacrib.png" width="80px" alt="Brandon P." /></a>&nbsp;&nbsp;
<a href="https://github.com/SeimusS"><img src="https://github.com/SeimusS.png" width="80px" alt="SeimusS" /></a>&nbsp;&nbsp;
<a href="https://github.com/HadrienKerlero"><img src="https://github.com/HadrienKerlero.png" width="80px" alt="HadrienKerlero" /></a>&nbsp;&nbsp;


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=maxdorninger/MediaManager&type=Date)](https://www.star-history.com/#maxdorninger/MediaManager&Date)


## Roadmap

- [x] support for more torrent indexers
- [x] fully automatic downloads
- [x] add tests
- [x] add more logs/errors
- [x] make API return proper error codes
- [x] optimize images for web in the backend
- [x] responsive ui
- [x] automatically update metadata of shows
- [x] automatically download new seasons/episodes of shows
- [x] add fallback to just copy files if hardlinks don't work
- [x] add check at startup if hardlinks work
- [x] create separate metadata relay service, so that api keys for TMDB and TVDB are not strictly needed
- [x] support for movies
- [x] expand README with more information and a quickstart guide
- [x] improve reliability of scheduled tasks
- [x] add notification system
- [x] add sequence diagrams to the documentation
- [x] add usenet support
- [x] provide example configuration files
- [x] make media sorting algorithm configurable
- [x] add support for transmission
- [x] add support for configuration via toml/yaml config file
- [ ] add in-depth documentation on the architecture of the codebase
- [ ] make indexer module multithreaded
- [ ] add delete button for movies/TV shows
- [ ] rework prowlarr module (select which indexers to use, etc.)
- [ ] _maybe_ rework the logo

See the [open issues](hhttps://maxdorninger.github.io/MediaManager/issues) for a full list of proposed features (and known issues).

## Screenshots

![Screenshot 2025-07-02 174732](https://github.com/user-attachments/assets/49fc18aa-b471-4be8-983e-c0ab240dfb73)
![Screenshot 2025-07-02 174342](https://github.com/user-attachments/assets/3a38953d-d0fa-4a7e-83d0-dd6e6427681c)
![Screenshot 2025-07-02 174616](https://github.com/user-attachments/assets/c3af4be8-b873-448c-8a4d-0d5db863aec7)
![Screenshot 2025-07-02 174416](https://github.com/user-attachments/assets/0d50f53b-64da-4243-8408-1d6fc85fe81b)
![Screenshot 2025-06-28 222908](https://github.com/user-attachments/assets/193e1afd-dabb-42a2-ab28-59f2784371c7)

## Developer Quick Start

For the developer guide see the [Developer Guide](https://maxdorninger.github.io/MediaManager/developer-guide.html).

<!-- LICENSE -->

## License

Distributed under the AGPL 3.0. See `LICENSE.txt` for more information.


<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

* [Thanks to Pawel Czerwinski for the image on the login screen](https://unsplash.com/@pawel_czerwinski)

