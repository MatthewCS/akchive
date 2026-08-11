from utils.statistics import MatchResults
import csv
import json
import re

ROUND_RE = r"Round (\d+)"


def get_schedule_results(
    raw_schedule: dict[int, list[list[str]]],
    raw_results: list[MatchResults],
    dqs_info: dict[str, list[dict]],
) -> dict[int, list[MatchResults]]:

    results: dict[int, list[MatchResults]] = {}

    for round in raw_schedule:

        results[round] = [
            match_result
            for trainers in raw_schedule[round]
            for match_result in raw_results
            if match_result.has_trainers(trainers)
        ]

        for trainers in raw_schedule[round]:

            match_has_been_played = (
                len(
                    [
                        1
                        for match_result in results[round]
                        if match_result.has_trainers(trainers)
                    ]
                )
                > 0
            )

            if not match_has_been_played:
                dummy_mr = MatchResults()
                dummy_mr.player_1 = trainers[0]
                dummy_mr.player_2 = trainers[1]
                game_is_dq = False

                # Check if this is a DQ
                if str(round) in dqs_info:
                    dqs_round = dqs_info[str(round)]
                    dq_games = [
                        [game for game in dq_game["Players"]] for dq_game in dqs_round
                    ]
                    dq_matchups = [
                        [dq_players[0]["Player"], dq_players[1]["Player"]]
                        for dq_players in dq_games
                    ]

                    matching_games = [
                        1
                        for dq_trainers in dq_matchups
                        if dummy_mr.has_trainers(dq_trainers)
                    ]
                    game_is_dq = len(matching_games) > 0

                # This is a DQ!
                if game_is_dq:
                    dq_info = [
                        players["Players"]
                        for players in dqs_info[str(round)]
                        if players["Players"][0]["Player"] in (trainers)
                    ][0]
                    dq_p1_info = [
                        info for info in dq_info if info["Player"] == trainers[0]
                    ][0]
                    dq_p2_info = [
                        info for info in dq_info if info["Player"] == trainers[1]
                    ][0]

                    winner: str | None = None
                    dq_info = "The match was not scheduled, so this game is counted as a DQ for both players."
                    if dq_p1_info["Win Credited"]:
                        winner = dq_p1_info["Player"]
                        dq_info = f"{winner} attempted to schedule this match and is credited with the win."
                    elif dq_p2_info["Win Credited"]:
                        winner = dq_p2_info["Player"]
                        dq_info = f"{winner} attempted to schedule this match and is credited with the win."

                    dummy_mr.disqualify(
                        dq_info,
                        dq_p1_info["Point Change"],
                        dq_p2_info["Point Change"],
                        winner,
                    )
                # Not a DQ - the game simply wasn't played!
                else:
                    dummy_mr.replay_url = "<GAME DATA NOT AVAILABLE>"

                results[round].append(dummy_mr)

    return results


def get_bowl_schedule_results(
    raw_schedule: dict[str, list[str]], raw_results: list[MatchResults]
) -> dict[str, MatchResults]:

    results: dict[str, MatchResults] = {}

    for bowl_game in raw_schedule:

        result_search = [
            match_result
            for match_result in raw_results
            if match_result.has_trainers(raw_schedule[bowl_game])
        ]
        if len(result_search) > 0:
            results[bowl_game] = result_search[0]
        else:
            dummy_mr = MatchResults()
            dummy_mr.player_1 = raw_schedule[bowl_game][0]
            dummy_mr.player_2 = raw_schedule[bowl_game][1]
            dummy_mr.replay_url = "<GAME DATA NOT AVAILABLE>"
            results[bowl_game] = dummy_mr

    return results


def schedule_from_csv(fp: str) -> dict[int, list[list[str]]]:

    round: int = -1
    results: dict[int, list[list[str]]] = {}

    with open(fp, "r", encoding="utf-8-sig") as f:

        reader = csv.reader(f)

        for row in reader:

            # Is this row denoting a round?
            match = re.match(ROUND_RE, row[0])
            if match:
                round = int(match.group(1))
                results[round] = []
            # Otherwise, get every match from this row
            for i in range(1, len(row) - 1):
                if row[i] == "vs":
                    results[round].append([row[i - 1], row[i + 1]])

    return results


def bowl_schedule_from_json(fp: str) -> dict[str, list[str]]:

    results: dict[str, list[str]] = {}

    with open(fp, "r") as f:

        results = json.load(f)

    return results


def update_names_in_schedule(
    names_dict: dict[str, str], schedule: dict[int, list[list[str]]]
) -> dict[int, list[list[str]]]:

    results: dict[int, list[list[str]]] = {}

    for round in schedule:

        results[round] = []

        for match in schedule[round]:

            results[round].append(
                [
                    names_dict[match[0]],
                    names_dict[match[1]],
                ]
            )

    return results


def update_names_in_bowl_schedule(
    names_dict: dict[str, str], schedule: dict[str, list[str]]
) -> dict[str, list[str]]:

    results: dict[str, list[str]] = {}

    for bowl_game in schedule:

        results[bowl_game] = [
            names_dict[schedule[bowl_game][0]],
            names_dict[schedule[bowl_game][1]],
        ]

    return results
