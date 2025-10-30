import logging

import requests

from media_manager.config import AllEncompassingConfig
from media_manager.indexer.config import ScoringRuleSet
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.movies.schemas import Movie
from media_manager.tv.schemas import Show

log = logging.getLogger(__name__)


def evaluate_indexer_query_result(
    query_result: IndexerQueryResult, ruleset: ScoringRuleSet
) -> (IndexerQueryResult, bool):
    title_rules = AllEncompassingConfig().indexers.title_scoring_rules
    indexer_flag_rules = AllEncompassingConfig().indexers.indexer_flag_scoring_rules
    for rule_name in ruleset.rule_names:
        for rule in title_rules:
            if rule.name == rule_name:
                log.debug(f"Applying rule {rule.name} to {query_result.title}")
                if (
                    any(
                        keyword.lower() in query_result.title.lower()
                        for keyword in rule.keywords
                    )
                    and not rule.negate
                ):
                    log.debug(
                        f"Rule {rule.name} with keywords {rule.keywords} matched for {query_result.title}"
                    )
                    query_result.score += rule.score_modifier
                elif (
                    not any(
                        keyword.lower() in query_result.title.lower()
                        for keyword in rule.keywords
                    )
                    and rule.negate
                ):
                    log.debug(
                        f"Negated rule {rule.name} with keywords {rule.keywords} matched for {query_result.title}"
                    )
                    query_result.score += rule.score_modifier
                else:
                    log.debug(
                        f"Rule {rule.name} with keywords {rule.keywords} did not match for {query_result.title}"
                    )
        for rule in indexer_flag_rules:
            if rule.name == rule_name:
                log.debug(f"Applying rule {rule.name} to {query_result.title}")
                if (
                    any(flag in query_result.flags for flag in rule.flags)
                    and not rule.negate
                ):
                    log.debug(
                        f"Rule {rule.name} with flags {rule.flags} matched for {query_result.title} with flags {query_result.flags}"
                    )
                    query_result.score += rule.score_modifier
                elif (
                    not any(flag in query_result.flags for flag in rule.flags)
                    and rule.negate
                ):
                    log.debug(
                        f"Negated rule {rule.name} with flags {rule.flags} matched for {query_result.title} with flags {query_result.flags}"
                    )
                    query_result.score += rule.score_modifier
                else:
                    log.debug(
                        f"Rule {rule.name} with flags {rule.flags} did not match for {query_result.title} with flags {query_result.flags}"
                    )
    if query_result.score <= 0:
        return query_result, False

    return query_result, True


def evaluate_indexer_query_results(
    query_results: list[IndexerQueryResult], media: Show | Movie, is_tv: bool
) -> list[IndexerQueryResult]:
    scoring_rulesets: list[ScoringRuleSet] = (
        AllEncompassingConfig().indexers.scoring_rule_sets
    )
    for ruleset in scoring_rulesets:
        if (
            (media.library in ruleset.libraries)
            or ("ALL_TV" in ruleset.libraries and is_tv)
            or ("ALL_MOVIES" in ruleset.libraries and not is_tv)
        ):
            log.debug(
                f"Applying scoring ruleset {ruleset.name} for {media.name} ({media.year})"
            )
            for result in query_results:
                log.debug(
                    f"Applying scoring ruleset {ruleset.name} for IndexerQueryResult {result.title} for {media.name} ({media.year})"
                )
                result, passed = evaluate_indexer_query_result(
                    query_result=result, ruleset=ruleset
                )
                if not passed:
                    log.debug(
                        f"Indexer query result {result.title} did not pass scoring ruleset {ruleset.name} with score {result.score}, removing from results."
                    )
                else:
                    log.debug(
                        f"Indexer query result {result.title} passed scoring ruleset {ruleset.name} with score {result.score}."
                    )

    query_results = [result for result in query_results if result.score >= 0]
    query_results.sort(reverse=True)
    return query_results


def follow_redirects_to_final_torrent_url(
    initial_url: str, session: requests.Session
) -> str | None:
    """
    Follows redirects to get the final torrent URL.
    :param session: a requests session
    :param initial_url: The initial URL to follow.
    :return: The final torrent URL or None if it fails.
    """
    current_url = initial_url
    final_url = None
    try:
        while True:
            response = session.get(current_url, allow_redirects=False)

            if 300 <= response.status_code < 400:
                redirect_url = response.headers.get("Location")
                if redirect_url.startswith("http://") or redirect_url.startswith(
                    "https://"
                ):
                    # It's an HTTP/HTTPS redirect, continue following
                    current_url = redirect_url
                    log.debug(f"Following HTTP/HTTPS redirect to: {current_url}")
                elif redirect_url.startswith("magnet:"):
                    # It's a Magnet URL, this is our final destination
                    final_url = redirect_url
                    log.debug(f"Reached Magnet URL: {final_url}")
                    break
                else:
                    log.error(
                        f"Reached unexpected non-HTTP/HTTPS/magnet URL: {redirect_url}"
                    )
                    raise RuntimeError(
                        f"Reached unexpected non-HTTP/HTTPS/magnet URL: {redirect_url}"
                    )
            else:
                # Not a redirect, so the current URL is the final one
                final_url = current_url
                break
    except requests.exceptions.RequestException as e:
        log.error(f"An error occurred during the request: {e}")
        raise RuntimeError(f"An error occurred during the request: {e}")
    if not final_url:
        log.error("Final URL could not be determined.")
        raise RuntimeError("Final URL could not be determined.")
    if final_url.startswith("http://") or final_url.startswith("https://"):
        log.debug("Final URL protocol: HTTP/HTTPS")
    elif final_url.startswith("magnet:"):
        log.debug("Final URL protocol: Magnet")
    else:
        log.error(f"Final URL is not a valid HTTP/HTTPS or Magnet URL: {final_url}")
        raise RuntimeError(
            f"Final URL is not a valid HTTP/HTTPS or Magnet URL: {final_url}"
        )

    return final_url
