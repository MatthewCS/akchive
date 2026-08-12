from .statistics import MatchResults, TrainerStats
from datetime import datetime
import joblib
import pandas as pd


def build_dataframes(
    league_name: str,
    rs_match_results: dict[int, list[MatchResults]],
    rs_trainer_stats: list[TrainerStats],
    bowl_game_results: dict[str, MatchResults],
    bowl_trainer_stats: list[TrainerStats],
    ps_match_results: dict[int, list[MatchResults]],
    ps_trainer_stats: list[TrainerStats],
    awards: dict[str, dict[str, str]],
    trainer_replacements: dict[str, str],
) -> dict[str, pd.DataFrame]:
    dfs_dict: dict[str, pd.DataFrame] = {}

    # These headers will be used for the regular season and postseason
    matches_summary_headers = (
        "Round",
        "Player 1",
        "Player 2",
        "Winner",
        "Margin of Victory",
        "Replay URL",
        "Disqualified",
        "DQ Info",
    )
    match_performances_headers = (
        "Round",
        "Pokémon Trainer",
        "Pokémon Name",
        "Total Kills",
        "Direct Kills",
        "Passive Kills",
        "Deaths",
    )
    trainer_pokemon_headers = (
        "Pokémon Name",
        "Pokémon Trainer",
        "Total Kills",
        "Direct Kills",
        "Passive Kills",
        "Deaths",
        "Matches Played",
        "Kills per Match",
        "Deaths per Match",
    )

    ################################
    #                              #
    # Regular season & league data #
    #                              #
    ################################
    rs_match_summaries = [
        [
            round,
            match.player_1,
            match.player_2,
            match.winner,
            match.margin_of_victory,
            match.replay_url,
            match.disqualified,
            match.dq_info,
        ]
        for round in rs_match_results
        for match in rs_match_results[round]
    ]
    rs_match_performances = []
    for round in rs_match_results:
        for match in rs_match_results[round]:
            for pokemon in match.player_1_pokemon + match.player_2_pokemon:
                rs_match_performances.append(
                    [
                        round,
                        pokemon.trainer,
                        pokemon.name,
                        pokemon.direct_kills + pokemon.passive_kills,
                        pokemon.direct_kills,
                        pokemon.passive_kills,
                        pokemon.deaths,
                    ]
                )
    rs_trainer_summaries_headers = (
        "Division",
        "Pokémon Trainer",
        "Wins",
        "Losses",
        "Differential",
        "Games Played",
    )
    rs_trainer_summaries = [
        [
            trainer.division,
            trainer.name,
            trainer.wins,
            trainer.losses,
            trainer.differential,
            trainer.wins + trainer.losses,
        ]
        for trainer in rs_trainer_stats
    ]
    # We want to merge players who were replaced with their fill-ins
    old_i: int = 0
    while old_i < len(rs_trainer_summaries):
        old_name = rs_trainer_summaries[old_i][1]

        if old_name in trainer_replacements:
            replacement_name = trainer_replacements[old_name]
            replacement_indicies = [
                i
                for i, val in enumerate(rs_trainer_summaries)
                if val[1] == replacement_name
            ]
            # If the replacement player has not played yet:
            if len(replacement_indicies) == 0:
                rs_trainer_summaries[old_i][1] = (
                    replacement_name + f" (prev. {old_name})"
                )
            # If the replacement player has played, merge records
            else:
                replacement_i = replacement_indicies[0]
                rs_trainer_summaries[old_i] = [
                    rs_trainer_summaries[old_i][0],
                    replacement_name + f" (prev. {old_name})",
                    rs_trainer_summaries[old_i][2]
                    + rs_trainer_summaries[replacement_i][2],
                    rs_trainer_summaries[old_i][3]
                    + rs_trainer_summaries[replacement_i][3],
                    rs_trainer_summaries[old_i][4]
                    + rs_trainer_summaries[replacement_i][4],
                    rs_trainer_summaries[old_i][5]
                    + rs_trainer_summaries[replacement_i][5],
                ]
                del rs_trainer_summaries[replacement_i]

        old_i += 1

    rs_trainer_pokemon = [
        [
            pokemon.name,
            trainer.name,
            pokemon.direct_kills + pokemon.passive_kills,
            pokemon.direct_kills,
            pokemon.passive_kills,
            pokemon.deaths,
            pokemon.matches_played,
            (pokemon.direct_kills + pokemon.passive_kills) / pokemon.matches_played,
            pokemon.deaths / pokemon.matches_played,
        ]
        for trainer in rs_trainer_stats
        for pokemon in trainer.pokemon.values()
    ]

    league_data_headers = (
        "League Name",
        "Last Updated",
        "Games Played (Total)",
        "Games Remaining",
        "Games per Season",
        "% of Games Completed",
    )
    unplayed_matches = [
        match
        for round in rs_match_results
        for match in rs_match_results[round]
        if match.replay_url == "<GAME DATA NOT AVAILABLE>"
    ]
    total_games_count = len(rs_match_summaries)
    remaining_games_count = len(unplayed_matches)
    total_games_played = total_games_count - remaining_games_count

    league_data_df = pd.DataFrame(
        [
            [
                league_name,
                datetime.now(),
                total_games_played,
                remaining_games_count,
                total_games_count,
                total_games_played / total_games_count,
            ]
        ],
        columns=league_data_headers,
        index=None,
    )
    rs_match_summaries_df = pd.DataFrame(
        rs_match_summaries, columns=matches_summary_headers, index=None
    )
    rs_match_performances_df = pd.DataFrame(
        rs_match_performances, columns=match_performances_headers, index=None
    )
    rs_match_performances_df.sort_values(
        ["Round", "Pokémon Trainer", "Pokémon Name"],
        ascending=[True, True, True],
        key=lambda col: col.str.lower() if col.dtype == "str" else col,
        inplace=True,
    )
    rs_trainer_summaries_df = pd.DataFrame(
        rs_trainer_summaries, columns=rs_trainer_summaries_headers, index=None
    )
    rs_trainer_summaries_df.sort_values(
        ["Division", "Wins", "Losses", "Differential", "Pokémon Trainer"],
        ascending=[True, False, True, False, True],
        key=lambda col: col.str.lower() if col.dtype == "str" else col,
        inplace=True,
    )
    rs_trainer_pokemon_df = pd.DataFrame(
        rs_trainer_pokemon, columns=trainer_pokemon_headers, index=None
    )
    rs_trainer_pokemon_df.sort_values(
        ["Pokémon Trainer", "Pokémon Name"],
        ascending=[True, True],
        key=lambda col: col.str.lower(),
        inplace=True,
    )

    ##################
    #                #
    # Bowl game data #
    #                #
    ##################
    bowl_summary_headers = (
        "Bowl Game",
        "Player 1",
        "Player 2",
        "Winner",
        "Margin of Victory",
        "Replay URL",
    )
    bowl_performances_headers = (
        "Bowl Game",
        "Pokémon Trainer",
        "Pokémon Name",
        "Total Kills",
        "Direct Kills",
        "Passive Kills",
        "Deaths",
    )
    bowl_game_summaries = [
        [
            bowl_game,
            bowl_result.player_1,
            bowl_result.player_2,
            bowl_result.winner,
            bowl_result.margin_of_victory,
            bowl_result.replay_url,
        ]
        for bowl_game, bowl_result in bowl_game_results.items()
    ]
    bowl_game_performances = []
    for bowl_game, bowl_result in bowl_game_results.items():
        for pokemon in bowl_result.player_1_pokemon + bowl_result.player_2_pokemon:
            bowl_game_performances.append(
                [
                    bowl_game,
                    pokemon.trainer,
                    pokemon.name,
                    pokemon.direct_kills + pokemon.passive_kills,
                    pokemon.direct_kills,
                    pokemon.passive_kills,
                    pokemon.deaths,
                ]
            )

    bowl_game_summaries_df = pd.DataFrame(
        bowl_game_summaries, columns=bowl_summary_headers, index=None
    )
    bowl_game_performances_df = pd.DataFrame(
        bowl_game_performances, columns=bowl_performances_headers, index=None
    )

    ####################
    #                  #
    # Poastseason data #
    #                  #
    ####################
    ps_match_summaries = [
        [
            round,
            match.player_1,
            match.player_2,
            match.winner,
            match.margin_of_victory,
            match.replay_url,
            match.disqualified,
            match.dq_info,
        ]
        for round in ps_match_results
        for match in ps_match_results[round]
    ]
    ps_match_performances = []
    for round in ps_match_results:
        for match in ps_match_results[round]:
            for pokemon in match.player_1_pokemon + match.player_2_pokemon:
                ps_match_performances.append(
                    [
                        round,
                        pokemon.trainer,
                        pokemon.name,
                        pokemon.direct_kills + pokemon.passive_kills,
                        pokemon.direct_kills,
                        pokemon.passive_kills,
                        pokemon.deaths,
                    ]
                )
    ps_trainer_pokemon = [
        [
            pokemon.name,
            trainer.name,
            pokemon.direct_kills + pokemon.passive_kills,
            pokemon.direct_kills,
            pokemon.passive_kills,
            pokemon.deaths,
            pokemon.matches_played,
            (pokemon.direct_kills + pokemon.passive_kills) / pokemon.matches_played,
            pokemon.deaths / pokemon.matches_played,
        ]
        for trainer in ps_trainer_stats
        for pokemon in trainer.pokemon.values()
    ]

    ps_match_summaries_df = pd.DataFrame(
        ps_match_summaries, columns=matches_summary_headers, index=None
    )
    ps_match_performances_df = pd.DataFrame(
        ps_match_performances, columns=match_performances_headers, index=None
    )
    ps_match_performances_df.sort_values(
        ["Round", "Pokémon Trainer", "Pokémon Name"],
        ascending=[True, True, True],
        key=lambda col: col.str.lower() if col.dtype == "str" else col,
        inplace=True,
    )
    ps_trainer_pokemon_df = pd.DataFrame(
        ps_trainer_pokemon, columns=trainer_pokemon_headers, index=None
    )
    ps_trainer_pokemon_df.sort_values(
        ["Pokémon Trainer", "Pokémon Name"],
        ascending=[True, True],
        key=lambda col: col.str.lower(),
        inplace=True,
    )

    ###############
    #             #
    # Awards data #
    #             #
    ###############
    awards_info_headers = ["Award Name", "Winner", "Description"]
    awards_info = [
        [award_name, award_data["Winner"], award_data["Description"]]
        for award_name, award_data in awards.items()
    ]
    awards_info_df = pd.DataFrame(
        awards_info,
        columns=awards_info_headers,
        index=None,
    )
    #############################
    #                           #
    # Build the dataframes dict #
    #                           #
    #############################
    dfs_dict["League Data"] = league_data_df

    dfs_dict["(RS) Match Summaries"] = rs_match_summaries_df
    dfs_dict["(RS) Match Performances"] = rs_match_performances_df
    dfs_dict["(RS) Trainer Summaries"] = rs_trainer_summaries_df
    dfs_dict["(RS) Trainer Pokémon"] = rs_trainer_pokemon_df

    dfs_dict["(BOWL) Game Summaries"] = bowl_game_summaries_df
    dfs_dict["(BOWL) Game Performances"] = bowl_game_performances_df

    dfs_dict["(PS) Match Summaries"] = ps_match_summaries_df
    dfs_dict["(PS) Match Performances"] = ps_match_performances_df
    dfs_dict["(PS) Trainer Pokémon"] = ps_trainer_pokemon_df

    dfs_dict["Awards"] = awards_info_df

    # Return the dataframes
    return dfs_dict


def export_data_joblib(
    fp: str,
    rs_match_results: dict[int, list[MatchResults]],
    rs_trainer_stats: list[TrainerStats],
    bowl_game_results: dict[str, MatchResults],
    bowl_trainer_stats: list[TrainerStats],
    ps_match_results: dict[int, list[MatchResults]],
    ps_trainer_stats: list[TrainerStats],
    awards: dict[str, dict[str, str]],
    trainer_replacements: dict[str, str],
    league_name: str,
) -> None:

    dfs_dict = build_dataframes(
        league_name,
        rs_match_results,
        rs_trainer_stats,
        bowl_game_results,
        bowl_trainer_stats,
        ps_match_results,
        ps_trainer_stats,
        awards,
        trainer_replacements,
    )

    joblib.dump(dfs_dict, fp, compress=("gzip", 3))


def export_data_xlsx(
    fp: str,
    rs_match_results: dict[int, list[MatchResults]],
    rs_trainer_stats: list[TrainerStats],
    bowl_game_results: dict[str, MatchResults],
    bowl_trainer_stats: list[TrainerStats],
    ps_match_results: dict[int, list[MatchResults]],
    ps_trainer_stats: list[TrainerStats],
    awards: dict[str, dict[str, str]],
    trainer_replacements: dict[str, str],
    league_name: str,
    league_icon_fp: str = "",
) -> None:

    dfs_dict = build_dataframes(
        league_name,
        rs_match_results,
        rs_trainer_stats,
        bowl_game_results,
        bowl_trainer_stats,
        ps_match_results,
        ps_trainer_stats,
        awards,
        trainer_replacements,
    )
    sheet_names = (
        ######################################
        #                                    #
        # Regular season & league worksheets #
        #                                    #
        ######################################
        "League Data",
        "(RS) Match Summaries",
        "(RS) Match Performances",
        "(RS) Trainer Summaries",
        "(RS) Trainer Pokémon",
        #########################
        #                       #
        # Postseason worksheets #
        #                       #
        #########################
        "(PS) Match Summaries",
        "(PS) Match Performances",
        "(PS) Trainer Pokémon",
        #########################
        #                       #
        # Bowl games worksheets #
        #                       #
        #########################
        "(BOWL) Game Summaries",
        "(BOWL) Game Performances",
        ###################
        #                 #
        # Award worksheet #
        #                 #
        ###################
        "Awards",
    )

    ##########################
    #                        #
    # Write to an .XLSX file #
    #                        #
    ##########################
    with pd.ExcelWriter(fp, engine="xlsxwriter") as writer:

        for sheet_name in sheet_names:
            dfs_dict[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)

        #######################
        #                     #
        # Workbook formatting #
        #                     #
        #######################
        book = writer.book

        format_datetime = book.add_format({"num_format": "ddd mmm d yyyy, h:mm AM/PM"})
        format_red = book.add_format(
            {"bold": True, "bg_color": "#672121", "font_color": "#FFFFFF"}
        )
        format_purple = book.add_format(
            {"bold": True, "bg_color": "#6C3BAA", "font_color": "#FFFFFF"}
        )
        format_orange = book.add_format(
            {"bold": True, "bg_color": "#BE5103", "font_color": "#FFFFFF"}
        )
        format_yellow = book.add_format(
            {"bold": True, "bg_color": "#FFE066", "font_color": "#000000"}
        )
        format_cyan = book.add_format(
            {"bold": True, "bg_color": "#83DFE9", "font_color": "#000000"}
        )
        format_percent = book.add_format(
            {
                "num_format": "0.00%",
            }
        )

        ###########################################
        #                                         #
        # Regular season & league data formatting #
        #                                         #
        ###########################################
        league_data_ws = writer.sheets["League Data"]
        match_summaries_ws = writer.sheets["(RS) Match Summaries"]
        rs_match_performances_ws = writer.sheets["(RS) Match Performances"]
        rs_trainer_summaries_ws = writer.sheets["(RS) Trainer Summaries"]
        rs_trainer_pokemon_ws = writer.sheets["(RS) Trainer Pokémon"]

        if league_icon_fp:
            league_data_ws.insert_image("B4", league_icon_fp)
        league_data_ws.add_table(
            0,
            0,
            dfs_dict["League Data"].shape[0],
            dfs_dict["League Data"].shape[1] - 1,
            {
                "columns": [
                    {"header": header} for header in dfs_dict["League Data"].columns
                ]
            },
        )
        league_data_ws.set_column(0, 0, 20)
        league_data_ws.set_column(1, 1, 24)
        league_data_ws.write_datetime(1, 1, datetime.now(), format_datetime)
        league_data_ws.set_column(2, dfs_dict["League Data"].shape[1] - 1, 16)
        league_data_ws.set_column(
            dfs_dict["League Data"].shape[1] - 1,
            dfs_dict["League Data"].shape[1] - 1,
            16,
            format_percent,
        )

        match_summaries_ws.add_table(
            0,
            0,
            dfs_dict["(RS) Match Summaries"].shape[0],
            dfs_dict["(RS) Match Summaries"].shape[1] - 1,
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(RS) Match Summaries"].columns
                ]
            },
        )
        match_summaries_ws.set_column(0, 0, 8)
        match_summaries_ws.set_column(
            1, dfs_dict["(RS) Match Summaries"].shape[1] - 2, 12
        )
        match_summaries_ws.set_column(
            dfs_dict["(RS) Match Summaries"].shape[1] - 1,
            dfs_dict["(RS) Match Summaries"].shape[1] - 1,
            100,
        )
        match_summaries_ws.conditional_format(
            1,
            5,
            dfs_dict["(RS) Match Summaries"].shape[0],
            5,
            {
                "type": "cell",
                "criteria": "=",
                "value": '"<GAME DATA NOT AVAILABLE>"',
                "format": format_red,
            },
        )

        rs_match_performances_ws.add_table(
            0,
            0,
            dfs_dict["(RS) Match Performances"].shape[0],
            dfs_dict["(RS) Match Performances"].shape[1] - 1,
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(RS) Match Performances"].columns
                ]
            },
        )
        rs_match_performances_ws.set_column(0, 0, 8)
        rs_match_performances_ws.set_column(1, 2, 24)
        rs_match_performances_ws.set_column(
            3, dfs_dict["(RS) Match Performances"].shape[1] - 1, 10
        )

        rs_trainer_summaries_ws.add_table(
            0,
            0,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            dfs_dict["(RS) Trainer Summaries"].shape[1] - 1,
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(RS) Trainer Summaries"].columns
                ]
            },
        )
        rs_trainer_summaries_ws.set_column(
            0, dfs_dict["(RS) Trainer Summaries"].shape[1] - 1, 16
        )
        rs_trainer_summaries_ws.set_column(1, 1, 24)
        rs_trainer_summaries_ws.set_column(2, 3, 8)
        rs_trainer_summaries_ws.set_column(4, 4, 12)
        rs_trainer_summaries_ws.conditional_format(
            1,
            4,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            4,
            {
                "type": "3_color_scale",
                "mid_color": "#DDDDDD",
            },
        )
        rs_trainer_summaries_ws.conditional_format(
            1,
            0,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            0,
            {
                "type": "cell",
                "criteria": "=",
                "value": '"Division 1"',
                "format": format_purple,
            },
        )
        rs_trainer_summaries_ws.conditional_format(
            1,
            0,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            0,
            {
                "type": "cell",
                "criteria": "=",
                "value": '"Division 2"',
                "format": format_orange,
            },
        )
        rs_trainer_summaries_ws.conditional_format(
            1,
            0,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            0,
            {
                "type": "cell",
                "criteria": "=",
                "value": '"Division 3"',
                "format": format_yellow,
            },
        )
        rs_trainer_summaries_ws.conditional_format(
            1,
            0,
            dfs_dict["(RS) Trainer Summaries"].shape[0],
            0,
            {
                "type": "cell",
                "criteria": "=",
                "value": '"Division 4"',
                "format": format_cyan,
            },
        )

        rs_trainer_pokemon_ws.add_table(
            0,
            0,
            dfs_dict["(RS) Trainer Pokémon"].shape[0],
            dfs_dict["(RS) Trainer Pokémon"].shape[1] - 1,
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(RS) Trainer Pokémon"].columns
                ]
            },
        )
        rs_trainer_pokemon_ws.set_column(0, 1, 24)
        rs_trainer_pokemon_ws.set_column(
            2, dfs_dict["(RS) Trainer Pokémon"].shape[1] - 3, 12
        )
        rs_trainer_pokemon_ws.set_column(
            dfs_dict["(RS) Trainer Pokémon"].shape[1] - 2,
            dfs_dict["(RS) Trainer Pokémon"].shape[1] - 1,
            18,
        )

        #########################
        #                       #
        # Bowl games formatting #
        #                       #
        #########################
        bowl_game_summaries_ws = writer.sheets["(BOWL) Game Summaries"]
        bowl_game_performances_ws = writer.sheets["(BOWL) Game Performances"]

        bowl_game_summaries_ws.add_table(
            0,
            0,
            dfs_dict["(BOWL) Game Summaries"].shape[0],
            dfs_dict["(BOWL) Game Summaries"].shape[1] - 1,
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(BOWL) Game Summaries"].columns
                ]
            },
        )
        bowl_game_summaries_ws.set_column(0, 3, 24)
        bowl_game_summaries_ws.set_column(4, 4, 12)
        bowl_game_summaries_ws.set_column(
            5, dfs_dict["(BOWL) Game Summaries"].shape[1] - 1, 36
        )

        bowl_game_performances_ws.add_table(
            0,
            0,
            dfs_dict["(BOWL) Game Performances"].shape[0],
            dfs_dict["(BOWL) Game Performances"].shape[1],
            {
                "columns": [
                    {"header": header}
                    for header in dfs_dict["(BOWL) Game Performances"].columns
                ]
            },
        )
        bowl_game_performances_ws.set_column(0, 2, 24)
        bowl_game_performances_ws.set_column(
            3, dfs_dict["(BOWL) Game Performances"].shape[1] - 1, 10
        )

        #####################
        #                   #
        # Awards formatting #
        #                   #
        #####################
        awards_info_ws = writer.sheets["Awards"]

        awards_info_ws.add_table(
            0,
            0,
            dfs_dict["Awards"].shape[0],
            dfs_dict["Awards"].shape[1] - 1,
            {"columns": [{"header": header} for header in dfs_dict["Awards"].columns]},
        )
        awards_info_ws.set_column(0, dfs_dict["Awards"].shape[1] - 1, 36)
