from pydantic_settings import BaseSettings


class ProwlarrConfig(BaseSettings):
    enabled: bool = False
    api_key: str = ""
    url: str = "http://localhost:9696"
    reject_torrents_on_url_error: bool = True


class JackettConfig(BaseSettings):
    enabled: bool = False
    api_key: str = ""
    url: str = "http://localhost:9696"
    indexers: list[str] = ["all"]


class ScoringRule(BaseSettings):
    name: str
    score_modifier: int = 0
    negate: bool = False


class TitleScoringRule(ScoringRule):
    keywords: list[str]


class IndexerFlagScoringRule(ScoringRule):
    flags: list[str]


class ScoringRuleSet(BaseSettings):
    name: str
    libraries: list[str] = []
    rule_names: list[str] = []


class IndexerConfig(BaseSettings):
    prowlarr: ProwlarrConfig = ProwlarrConfig()
    jackett: JackettConfig = JackettConfig()
    title_scoring_rules: list[TitleScoringRule] = []
    indexer_flag_scoring_rules: list[IndexerFlagScoringRule] = []
    scoring_rule_sets: list[ScoringRuleSet] = []
