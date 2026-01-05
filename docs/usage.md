# Usage

If you are coming from Radarr or Sonarr you will find that MediaManager does things a bit differently. Instead of completely automatically downloading and managing your media, MediaManager focuses on providing an easy-to-use interface to guide you through the process of finding and downloading media. Advanced features like multiple qualities of a show/movie necessitate such a paradigm shift. So here is a quick step-by-step guide to get you started:

#### Downloading/Requesting a show

{% stepper %}
{% step %}
### Add the show

Add a show on the "Add Show" page. After adding the show you will be redirected to the show's page.
{% endstep %}

{% step %}
### Request season(s)

Click the "Request Season" button on the show's page. Select one or more seasons that you want to download.
{% endstep %}

{% step %}
### Select qualities

Select the "Min Quality" — the minimum resolution of the content to download.\
Select the "Wanted Quality" — the **maximum** resolution of the content to download.
{% endstep %}

{% step %}
### Submit request

Click "Submit request". This is not the last step: an administrator must first approve your request for download. Only after approval will the requested content be downloaded.
{% endstep %}

{% step %}
### Finished

Congratulation! You've downloaded a show (after admin approval).
{% endstep %}
{% endstepper %}

#### Requesting a show (as an admin)

{% stepper %}
{% step %}
### Add the show

Add a show on the "Add Show" page. After adding the show you will be redirected to the show's page.
{% endstep %}

{% step %}
### Request season(s)

Click the "Request Season" button on the show's page. Select one or more seasons that you want to download.
{% endstep %}

{% step %}
### Select qualities

Select the "Min Quality" — the minimum resolution of the content to download.\
Select the "Wanted Quality" — the **maximum** resolution of the content to download.
{% endstep %}

{% step %}
### Submit request (auto-approved)

Click "Submit request". As an admin, your request will be automatically approved.
{% endstep %}

{% step %}
### Finished

Congratulation! You've downloaded a show.
{% endstep %}
{% endstepper %}

#### Downloading a show (admin-only)

You can only directly download a show if you are an admin!

{% stepper %}
{% step %}
### Go to the show's page

Open the show's page that contains the season you wish to download.
{% endstep %}

{% step %}
### Start download

Click the "Download Season" button.
{% endstep %}

{% step %}
### Enter season number

Enter the season number that you want to download.
{% endstep %}

{% step %}
### Optional file path suffix

Optionally select the "File Path Suffix". Note: **it needs to be unique per season per show!**
{% endstep %}

{% step %}
### Choose torrent and download

Click "Download" on the torrent that you want to download.
{% endstep %}

{% step %}
### Finished

Congratulation! You've downloaded a show.
{% endstep %}
{% endstepper %}

#### Managing requests

Users need their requests to be approved by an admin. To manage requests:

{% stepper %}
{% step %}
### Open Requests page

Go to the "Requests" page.
{% endstep %}

{% step %}
### Approve, delete or modify

From the Requests page you can approve, delete, or modify a user's request.
{% endstep %}
{% endstepper %}
