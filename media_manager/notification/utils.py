import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from media_manager.config import AllEncompassingConfig

log = logging.getLogger(__name__)


def send_email(subject: str, html: str, addressee: str) -> None:
    email_conf = AllEncompassingConfig().notifications.smtp_config
    message = MIMEMultipart()
    message["From"] = email_conf.from_email
    message["To"] = addressee
    message["Subject"] = str(subject)
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP(email_conf.smtp_host, email_conf.smtp_port) as server:
        if email_conf.use_tls:
            server.starttls()
        server.login(email_conf.smtp_user, email_conf.smtp_password)
        server.sendmail(email_conf.from_email, addressee, message.as_string())

    log.info(f"Successfully sent email to {addressee} with subject: {subject}")


def detect_unknown_media(path: Path) -> list[Path]:
    libraries = []
    libraries.extend(AllEncompassingConfig().misc.movie_libraries)
    libraries.extend(AllEncompassingConfig().misc.tv_libraries)

    show_dirs = path.glob("*")
    log.debug(f"Using Directory {path}")
    unknown_tv_shows = []
    for media_dir in show_dirs:
        # check if directory is one created by MediaManager (contins [tmdbd/tvdbid-0000) or if it is a library
        if (
            re.search(r"\[(?:tmdbid|tvdbid)-\d+]", media_dir.name, re.IGNORECASE)
            or media_dir.absolute()
            in [Path(library.path).absolute() for library in libraries]
            or media_dir.name.startswith(".")
        ):
            log.debug(f"MediaManager directory detected: {media_dir.name}")
        else:
            log.info(f"Detected unknown media directory: {media_dir.name}")
            unknown_tv_shows.append(media_dir)
    return unknown_tv_shows
