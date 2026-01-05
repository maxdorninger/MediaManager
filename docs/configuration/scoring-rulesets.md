# Scoring Rulesets

Scoring rulesets in MediaManager allow you to flexibly control which releases are preferred or avoided when searching for media. Each ruleset is a collection of scoring rules that can be assigned to one or more libraries. When MediaManager evaluates releases, it applies the relevant ruleset(s) to adjust the score of each result, influencing which releases are selected for download.

## How Rulesets Work

* Rulesets are defined in the configuration and contain a list of rule names and the libraries they apply to.
* Scoring rules can target keywords in release titles or specific indexer flags.
* When searching for a release, MediaManager checks which library the media belongs to and applies the corresponding ruleset.

## Rules

Rules define how MediaManager scores releases based on their titles or indexer flags. You can create rules that:

* Prefer releases with specific codecs (e.g., H.265 over H.264).
* Avoid releases with certain keywords (e.g., "CAM", "TS", "Nuked").
* Reject releases that do not meet certain criteria (e.g., non-freeleech releases).
* and more.

{% hint style="info" %}
The keywords and flags are compared case-insensitively.
{% endhint %}

### Title Rules

Title rules allow you to adjust the score of a release based on the presence (or absence) of specific keywords in the release title. This is useful for preferring or avoiding certain encodings, sources, or other characteristics that are typically included in release names.

Each title rule consists of:

* `name`\
  A unique identifier for the rule.
* `keywords`\
  List of keywords to search for in the release title.
* `score_modifier`\
  Amount to add or subtract from the score if a keyword matches.
* `negate`\
  If `true`, the rule applies when none of the keywords are present.

Examples for Title Rules

{% code title="config.toml" %}
```toml
[[indexers.title_scoring_rules]]
name = "prefer_h265"
keywords = ["h265", "hevc", "x265"]
score_modifier = 100
negate = false

[[indexers.title_scoring_rules]]
name = "avoid_cam"
keywords = ["cam", "ts"]
score_modifier = -10000
negate = false
```
{% endcode %}

* The first rule increases the score for releases containing "h265", "hevc", or "x265".
* The second rule heavily penalizes releases containing "cam" or "ts".

If `negate` is set to `true`, the `score_modifier` is applied only if none of the keywords are found in the title.

### Indexer Flag Rules

Indexer flag rules adjust the score based on flags provided by the indexer (such as `freeleech`, `nuked`, etc). These flags are often used to indicate special properties or warnings about a release.

Each indexer flag rule consists of:

* `name`\
  A unique identifier for the rule.
* `flags`\
  List of indexer flags to match.
* `score_modifier`\
  Amount to add or subtract from the score if a flag matches.
* `negate`\
  If `true`, the rule applies when none of the flags are present.

Examples for Indexer Flag Rules

{% code title="config.toml" %}
```toml
[[indexers.indexer_flag_scoring_rules]]
name = "reject_non_freeleech"
flags = ["freeleech", "freeleech75"]
score_modifier = -10000
negate = true

[[indexers.indexer_flag_scoring_rules]]
name = "reject_nuked"
flags = ["nuked"]
score_modifier = -10000
negate = false
```
{% endcode %}

* The first rule penalizes releases that do not have the "freeleech" or "freeleech75" flag.
* The second rule penalizes releases that are marked as "nuked".

If `negate` is set to `true`, the `score_modifier` is applied only if none of the flags are present on the release.

## Example

{% code title="config.toml" %}
```toml
[[indexers.scoring_rule_sets]]
name = "default"
libraries = ["ALL_TV", "ALL_MOVIES"]
rule_names = ["prefer_h265", "avoid_cam", "reject_nuked"]

[[indexers.scoring_rule_sets]]
name = "strict_quality"
libraries = ["ALL_MOVIES"]
rule_names = ["prefer_h265", "avoid_cam", "reject_non_freeleech"]
```
{% endcode %}

## Libraries

The libraries that are mentioned in the preceding example are explained in greater detail in the [Library config section](custom-libraries.md).

### Special Libraries

You can use special library names in your rulesets:

* `ALL_TV`: Applies the ruleset to all TV libraries.
* `ALL_MOVIES`: Applies the ruleset to all movie libraries.
* `Default`: Applies the ruleset to all media that is not part of a custom library.

This allows you to set global rules for all TV or movie content, or provide fallback rules for uncategorized media.

{% hint style="info" %}
You don't need to create lots of libraries with different directories, multiple libraries can share the same directory. You can set multiple (unlimited) libraries to the default directory `/data/movies` or `/data/tv` and use different rulesets with them.
{% endhint %}

## Relation to Sonarr/Radarr Profiles

MediaManager's scoring rules and rulesets system is an alternative to Sonarr's Quality, Custom, and Release Profiles. This system is designed to be more intuitive and flexible.

* Quality Profiles: Use scoring rules to prefer or avoid certain codecs, resolutions, or other quality indicators.
* Custom/Release Profiles: Use title or flag-based rules to match or exclude releases based on keywords or indexer flags.

This approach provides a powerful and transparent way to fine-tune your automation.
