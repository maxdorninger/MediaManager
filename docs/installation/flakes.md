# Nix Flakes

!!! note
    This is a community contribution and not officially supported by the MediaManager team, but included here for convenience. 

    *Please report issues with this method at the [corresponding GitHub repository](https://github.com/strangeglyph/mediamanager-nix).*

## Prerequisites

This guide assumes that your system is a flakes-based NixOS installation. Hosting MediaManager on a subpath (e.g. `yourdomain.com/mediamanager`) is currently not supported, though contributions to add support are welcome.

## Importing the community flake

To use the community-provided flake and module, first import it in your own flake, for example:

```nix
{
  description = "An example NixOS configuration";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixos-unstable"; };
    
    mediamanager-nix = {
      url = "github:strangeglyph/mediamanager-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{
    nixpkgs,
    mediamanager-nix,
    ...
  }: {
    nixosConfigurations.your-system = nixpkgs.lib.nixosSystem {
      modules = [
        mediamanager-nix.nixosModules.default
      ];
    };
  };
}
```

## Configuration

The flake provides a simple module to set up a MediaManager systemd service. To enable it, set

```nix
{
  config = {
    services.media-manager = {
      enable = true;
    };
  };
}
```

You will either want to set `services.media-manager.dataDir`, which will provide sensible defaults for the settings 
`misc.{image,movie,tv,torrent}_directory`, or provide specific paths yourself.

The host and port that MediaManager listens on can be set using `services.media-manager.{host,port}`.

To configure MediaManager, use `services.media-manager.settings`, which follows the same structure as the MediaManager 
`config.toml`. To provision secrets, set `services.media-manager.environmentFile` to a protected file, for example one
provided by [agenix](https://github.com/ryantm/agenix) or [sops-nix](https://github.com/Mic92/sops-nix). 
See [Configuration](../configuration/README.md#configuring-secrets) for guidance on using environment variables.


!!! warning
    Do not place secrets in the nix store, as it is world-readable.

## Automatic Postgres Setup

As a convenience feature, the module provides a simple Postgres setup that can be enabled with `services.media-manager.postgres.enable`. This sets up a database user named `services.media-manager.postgres.user` and a database with the same name. Provided the user of the systemd service wasn't changed, authentication should work automatically for unix socket connections (the default mediamanager-nix settings). 

For advanced setups, please refer to the NixOS manual.

## Example Configuration

Here is a minimal complete flake for a MediaManager setup:

```nix
{
  description = "An example NixOS configuration";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixos-unstable"; };
    mediamanager-nix = {
      url = "github:strangeglyph/mediamanager-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs@{
    nixpkgs,
    mediamanager-nix,
    ...
  }: {
    nixosConfigurations.your-system = nixpkgs.lib.nixosSystem {
      imports = [
        mediamanager-nix.nixosModules.default
      ];

      config = {
        services.media-manager = {
          enable = true;
          postgres.enable = true;
          port = 12345;
          dataDir = "/tmp";
          settings = {
            misc.frontend_url = "http://[::1]:12345";
          };
        };

        systemd.tmpfiles.settings."10-mediamanager" = {
          "/tmp/movies".d = { user = config.services.media-manager.user; };
          "/tmp/shows".d = { user = config.services.media-manager.user; };
          "/tmp/images".d = { user = config.services.media-manager.user; };
          "/tmp/torrents".d = { user = config.services.media-manager.user; };
        };
      };
    };
  };
}
```