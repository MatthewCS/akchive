from utils.statistics import MatchResults
import csv
import json
import re

ROUND_RE = r"Round (\d+)"


def get_schedule_results(
    raw_schedule: dict[int, list[list[str]]], raw_results: list[MatchResults]
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
                        str(match_result)
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
