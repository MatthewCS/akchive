from .statistics import MatchResults, PokemonStats, TrainerStats
from enum import Enum
import re


class ParserStates(Enum):
    RESULT = 0
    PLAYER_1_NAME = 1
    PLAYER_1_POKEMON = 2
    PLAYER_2_NAME = 3
    PLAYER_2_POKEMON = 4
    REPLAY_URL = 5
    HISTORY_URL = 6
    GARBAGE = 7


class ResultsParser(object):
    _RESULT_RE = r"Result:\s+(.+) won (\d)-\d"
    _PLAYER_NAME_RE = r"(.+):"
    _POKEMON_FULL_STATS_RE = (
        r"(.+) has (\d+) direct kills, (\d+) passive kills, and (\d+) deaths."
    )
    _POKEMON_PARTIAL_STATS_RE = r"(.+) (\d+) (\d+)"
    _REPLAY_URL_RE = r"Replay: (\S+)"
    _HISTORY_URL_RE = r"History: (\S+)"
    _divisions_data: dict[str, str]
    _alias_data: dict[str, dict[str, str]]
    _replacements_data: dict[str, str]
    trainer_stats: list[TrainerStats]
    results: list[MatchResults]

    def __init__(
        self,
        porygon_message: str = "",
        divisions: dict[str, list[str]] | None = None,
        aliases: dict[str, dict[str, str]] | None = None,
        replacements: dict[str, str] | None = None,
    ):
        self._divisions_data = {}
        self._alias_data = {}
        self._replacements_data = {}
        self.trainer_stats = []
        self.results = []

        if divisions:
            for division, players in divisions.items():
                for player in players:
                    self._divisions_data[player] = division
        if aliases:
            self._alias_data = aliases
        else:
            self._alias_data = {"showdown names": {}, "player names": {}}
        if replacements:
            self._replacements_data = replacements

        if porygon_message:
            self.ingest(porygon_message)

    def _build_trainer_stats(self):

        stats: dict[str, TrainerStats] = {}

        for match in self.results:

            # Look at player 1, then player 2
            if match.player_1 not in stats:
                stats[match.player_1] = TrainerStats(match.player_1)
                if match.player_1 in self._divisions_data:
                    stats[match.player_1].division = self._divisions_data[
                        match.player_1
                    ]
            stats[match.player_1].add_match(match)

            if match.player_2 not in stats:
                stats[match.player_2] = TrainerStats(match.player_2)
                if match.player_2 in self._divisions_data:
                    stats[match.player_2].division = self._divisions_data[
                        match.player_2
                    ]
            stats[match.player_2].add_match(match)

        self.trainer_stats = list(stats.values())

    def ingest(self, porygon_message):

        state = ParserStates.RESULT

        for line in porygon_message.split("\n"):

            if state == ParserStates.RESULT:
                # We are on the result - line #1
                # This line reads "Result:  <PLAYER_NAME> won <SCORE>"
                match = re.match(self._RESULT_RE, line)
                if match:
                    self.results.append(MatchResults())

                    winner = match.group(1)
                    if winner in self._alias_data["showdown names"]:
                        winner = self._alias_data["showdown names"][winner]

                    self.results[-1].winner = winner
                    self.results[-1].margin_of_victory = int(match.group(2))
                    state = ParserStates.PLAYER_1_NAME

            elif state == ParserStates.PLAYER_1_NAME:
                match = re.match(self._PLAYER_NAME_RE, line)
                if match:
                    player_name = match.group(1)
                    if player_name in self._alias_data["showdown names"]:
                        player_name = self._alias_data["showdown names"][player_name]
                    self.results[-1].player_1 = player_name
                    state = ParserStates.PLAYER_1_POKEMON

            elif state == ParserStates.PLAYER_1_POKEMON:
                full_match = re.match(self._POKEMON_FULL_STATS_RE, line)
                partial_match = re.match(self._POKEMON_PARTIAL_STATS_RE, line)
                if full_match:
                    self.results[-1].player_1_pokemon.append(
                        PokemonStats(
                            full_match.group(1),
                            self.results[-1].player_1,
                            int(full_match.group(2)),
                            int(full_match.group(3)),
                            int(full_match.group(4)),
                        )
                    )
                elif partial_match:
                    self.results[-1].player_1_pokemon.append(
                        PokemonStats(
                            partial_match.group(1),
                            self.results[-1].player_1,
                            int(partial_match.group(2)),
                            0,
                            int(partial_match.group(3)),
                        )
                    )
                else:
                    state = ParserStates.PLAYER_2_NAME

            elif state == ParserStates.PLAYER_2_NAME:
                match = re.match(self._PLAYER_NAME_RE, line)
                if match:
                    player_name = match.group(1)
                    if player_name in self._alias_data["showdown names"]:
                        player_name = self._alias_data["showdown names"][player_name]
                    self.results[-1].player_2 = player_name
                    state = ParserStates.PLAYER_2_POKEMON

            elif state == ParserStates.PLAYER_2_POKEMON:
                full_match = re.match(self._POKEMON_FULL_STATS_RE, line)
                partial_match = re.match(self._POKEMON_PARTIAL_STATS_RE, line)
                if full_match:
                    self.results[-1].player_2_pokemon.append(
                        PokemonStats(
                            full_match.group(1),
                            self.results[-1].player_2,
                            int(full_match.group(2)),
                            int(full_match.group(3)),
                            int(full_match.group(4)),
                        )
                    )
                elif partial_match:
                    self.results[-1].player_2_pokemon.append(
                        PokemonStats(
                            partial_match.group(1),
                            self.results[-1].player_2,
                            int(partial_match.group(2)),
                            0,
                            int(partial_match.group(3)),
                        )
                    )
                else:
                    state = ParserStates.REPLAY_URL

            elif state == ParserStates.REPLAY_URL:
                match = re.match(self._REPLAY_URL_RE, line)
                if match:
                    self.results[-1].replay_url = match.group(1)
                    state = ParserStates.HISTORY_URL

            elif state == ParserStates.HISTORY_URL:
                match = re.match(self._HISTORY_URL_RE, line)
                if match:
                    # When we've found the history URL, match the next message
                    state = ParserStates.RESULT

        self._build_trainer_stats()

    def __str__(self):

        return "\n\n\n".join([str(result) for result in self.results])
