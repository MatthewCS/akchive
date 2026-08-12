from utils import exporters
from utils.build_schedule import (
    bowl_schedule_from_json,
    get_bowl_schedule_results,
    get_schedule_results,
    schedule_from_csv,
    update_names_in_bowl_schedule,
    update_names_in_schedule,
)
from utils.parser import ResultsParser
import json

# Player info
TEST_ALIASES_FP = "./input/season_2/player info/aliases.json"
TEST_DIVISIONS_FP = "./input/season_2/player info/divisions.json"
TEST_REPLACEMENTS_FP = "./input/season_2/player info/replacements.json"
# Regular season info
TEST_MESSAGES_FP = "./input/season_2/regular season/games.txt"
TEST_SCHEDULE_FP = "./input/season_2/regular season/schedule.csv"
TEST_DQ_FP = "./input/season_2/regular season/disqualifications.json"
# Bowl info
TEST_BOWL_MESSAGES_FP = "./input/season_2/bowls/bowl_games.txt"
TEST_BOWL_SCHEDULE_FP = "./input/season_2/bowls/bowl_schedule.json"
# Postseason info
TEST_POSTSEASON_MESSAGES_FP = "./input/season_2/postseason/postseason_games.txt"
TEST_POSTSEASON_SCHEDULE_FP = "./input/season_2/postseason/postseason_schedule.csv"
# Award info
TEST_AWARDS_FP = "./input/season_2/awards/awards.json"


def read_test_files():

    test_messages = ""
    test_divisions = {}
    test_aliases = {}
    test_replacements = {}
    test_schedule = {}
    test_dqs = {}

    with open(TEST_MESSAGES_FP, "r") as f:
        test_messages = f.read()

    test_schedule = schedule_from_csv(TEST_SCHEDULE_FP)

    with open(TEST_DQ_FP, "r") as f:
        test_dqs = json.load(f)

    with open(TEST_DIVISIONS_FP, "r") as f:
        test_divisions = json.load(f)

    with open(TEST_ALIASES_FP, "r") as f:
        test_aliases = json.load(f)

    with open(TEST_REPLACEMENTS_FP, "r") as f:
        test_replacements = json.load(f)

    with open(TEST_BOWL_MESSAGES_FP, "r") as f:
        test_bowl_messages = f.read()

    test_bowl_schedule = bowl_schedule_from_json(TEST_BOWL_SCHEDULE_FP)

    with open(TEST_POSTSEASON_MESSAGES_FP, "r") as f:
        test_postseason_messages = f.read()

    test_postseason_schedule = schedule_from_csv(TEST_POSTSEASON_SCHEDULE_FP)

    with open(TEST_AWARDS_FP, "r") as f:
        test_awards_info = json.load(f)

    return (
        test_messages,
        test_divisions,
        test_aliases,
        test_replacements,
        test_schedule,
        test_dqs,
        test_bowl_messages,
        test_bowl_schedule,
        test_postseason_messages,
        test_postseason_schedule,
        test_awards_info,
    )


if __name__ == "__main__":

    (
        rs_contents,
        divisions,
        aliases,
        replacements,
        rs_schedule,
        rs_disquals,
        bowl_contents,
        bowl_schedule,
        ps_contents,
        ps_schedule,
        awards_info,
    ) = read_test_files()

    # Regular season
    rs_schedule = update_names_in_schedule(aliases["schedule names"], rs_schedule)
    rs_results_parser = ResultsParser(rs_contents, divisions, aliases, replacements)
    rs_schedule_results = get_schedule_results(
        rs_schedule, rs_results_parser.results, rs_disquals
    )
    rs_trainer_stats = rs_results_parser.trainer_stats
    for round in rs_schedule_results:
        for result in rs_schedule_results[round]:
            if result.disqualified:
                player_1_idx = [
                    i
                    for i, stats in enumerate(rs_trainer_stats)
                    if stats.name == result.player_1
                ][0]
                player_2_idx = [
                    i
                    for i, stats in enumerate(rs_trainer_stats)
                    if stats.name == result.player_2
                ][0]

                # Update player 1
                rs_trainer_stats[player_1_idx].differential += result.p1_dq_score
                if result.winner == result.player_1:
                    rs_trainer_stats[player_1_idx].wins += 1
                else:
                    rs_trainer_stats[player_1_idx].losses += 1

                # Update player 2
                rs_trainer_stats[player_2_idx].differential += result.p2_dq_score
                if result.winner == result.player_2:
                    rs_trainer_stats[player_2_idx].wins += 1
                else:
                    rs_trainer_stats[player_2_idx].losses += 1

    # Bowl games
    bowl_schedule = update_names_in_bowl_schedule(
        aliases["schedule names"], bowl_schedule
    )
    bowl_results_parser = ResultsParser(bowl_contents, divisions, aliases, replacements)
    bowl_schedule_results = get_bowl_schedule_results(
        bowl_schedule, bowl_results_parser.results
    )

    # Playoffs
    ps_schedule = update_names_in_schedule(aliases["schedule names"], ps_schedule)
    ps_results_parser = ResultsParser(ps_contents, divisions, aliases, replacements)
    ps_schedule_results = get_schedule_results(
        ps_schedule, ps_results_parser.results, {}
    )

    print("Parsed results files")

    # Zoroark-H breaks Porygon, so I want to see a list of every game it played in.
    print("ZOROARK-H WATCH!")
    print("  Regular season:")
    for week in rs_schedule_results:

        for result in rs_schedule_results[week]:

            # Is Zoroark-H in this game?
            if result.has_pokemon("Zoroark-Hisui"):

                print(
                    f"    WEEK {week}: {result.player_1} vs {result.player_2} : {result.replay_url}".format(
                        week, result
                    )
                )
    print("  Bowl games:")
    for bowl_game in bowl_schedule_results:

        # Is Zoroark-H in this game?
        result = bowl_schedule_results[bowl_game]
        if result.has_pokemon("Zoroark-Hisui"):

            print(
                f"    {bowl_game}: {result.player_1} vs {result.player_2} : {result.replay_url}".format(
                    bowl_game, result
                )
            )
    print("Please ensure that each of the listed games is accurate!")

    exporters.export_data_xlsx(
        "./output/season 2.xlsx",
        rs_schedule_results,
        rs_trainer_stats,
        bowl_schedule_results,
        bowl_results_parser.trainer_stats,
        ps_schedule_results,
        ps_results_parser.trainer_stats,
        awards_info,
        replacements,
        "Viral Akdraft Season 2",
        "./input/season_2/ChatDiPiTi.png",
    )
    exporters.export_data_joblib(
        "./output/season 2.gzip",
        rs_schedule_results,
        rs_trainer_stats,
        bowl_schedule_results,
        bowl_results_parser.trainer_stats,
        ps_schedule_results,
        ps_results_parser.trainer_stats,
        awards_info,
        replacements,
        "Viral Akdraft Season 2",
    )
