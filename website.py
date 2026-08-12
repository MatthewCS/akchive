import datetime
import glob
import joblib
import streamlit as st
import pandas as pd
from typing import Literal

INPUT_FOLDER = "./parser/output/"


def read_input_xlsx_files() -> list[dict[str, pd.DataFrame]]:

    dataframes: list[dict[str, pd.DataFrame]] = []

    for filepath in list(glob.glob(INPUT_FOLDER + "*.gzip")):

        dataframes.append(joblib.load(filepath))

    return dataframes


def landing():

    st.set_page_config(page_title="About - Akchive", page_icon="🔥", layout="centered")
    st.title("Welcome to the Akchive!")
    st.subheader("This website archives Akleague data, from season 2 onward.")
    st.text(
        "Akleague is a recurring Pokémon draft league. Feel free to watch our matches!"
    )
    with st.container(
        horizontal_alignment="center",
        vertical_alignment="center",
    ):
        with st.container(border=True, width="content", height="content"):
            st.image(
                "static/geoff.png",
                caption='"We\'re so excited to play our next games!" -Geoff K.',
                width="content",
            )


def build_matches(round: int | str, round_df, count_games_in_round: bool = True):

    if type(round) is int:
        st.subheader(f"Round {round}")
    else:
        st.subheader(round)

    if count_games_in_round:
        # How many games in this round have been played?
        games_in_round = round_df.shape[0]
        games_played = len(
            round_df.loc[(~round_df["Disqualified"]) & (round_df["Winner"] != "")]
        )
        games_disqualified = len(round_df.loc[round_df["Disqualified"]])
        games_unplayed = games_in_round - games_played - games_disqualified

        md_str = ""
        # If all games have been played
        if games_played + games_disqualified == games_in_round:
            md_str += (
                "This round is finished!  \n"
                + f"**{games_played}** matches have been played. "
            )
        else:
            md_str = (
                f"**{games_played}** matches have been played. "
                + f"**{games_unplayed}** matches have yet to be played!"
            )
        if games_disqualified > 0:
            md_str += "  \n"
            md_str += f"**{games_disqualified}** disqualifications were given."

        st.markdown(md_str)

    for _, row in round_df.iterrows():
        with st.container(border=True):
            left, right = st.columns(
                2,
                vertical_alignment="center",
                gap="xxsmall",
            )

            with left:
                st.markdown("""**{p1}**  
                    vs. **{p2}**""".format(p1=row["Player 1"], p2=row["Player 2"]))

            with right:
                # Is this game a DQ?
                if "Disqualified" in row and row["Disqualified"]:
                    st.markdown(f"**Disqualified**  \n{row["DQ Info"]}")
                # Has this game been played yet?
                elif row["Winner"]:
                    st.markdown(
                        f"Winner: **{row["Winner"]}** (**+{row["Margin of Victory"]}**)"
                    )

                    st.link_button(
                        "Watch Replay",
                        row["Replay URL"],
                        type="primary",
                    )

                else:
                    st.caption("MATCH HAS YET TO BE PLAYED")


def build_schedule_tab(
    summaries_df: pd.DataFrame,
    rounds_tab_text: str = "Rounds",
    key: str = "Round",
    count_games_in_round: bool = True,
    style: Literal["Container", "Tab"] = "Container",
):

    by_round, full_table = st.tabs([rounds_tab_text, "Full Table"])

    with by_round:

        rounds = summaries_df[key].unique().tolist()
        if style == "Container":
            for round in rounds:
                round_df = summaries_df.loc[summaries_df[key] == round]
                build_matches(round, round_df, count_games_in_round)

        elif style == "Tab":
            round_strs = []
            if type(rounds[0] is int):
                round_strs = [f"Round {n}" for n in rounds]
            else:
                round_strs = rounds

            round_tabs = st.tabs(round_strs)

            for i in range(len(round_tabs)):
                with round_tabs[i]:
                    round_df = summaries_df.loc[summaries_df[key] == rounds[i]]
                    build_matches(i + 1, round_df, count_games_in_round)

    with full_table:

        summaries_df["Replay URL"] = summaries_df["Replay URL"].str.replace(
            "<GAME DATA NOT AVAILABLE>", ""
        )

        st.dataframe(
            summaries_df,
            column_config={
                "Replay URL": st.column_config.LinkColumn(),
            },
            height="content",
            hide_index=True,
        )


def build_page(frames: dict[str, pd.DataFrame]):

    league_name = frames["League Data"].iloc[0]["League Name"]
    games_remaining = frames["League Data"].iloc[0]["Games Remaining"]

    st.set_page_config(
        page_title=f"{league_name} - Akchive", page_icon="🔥", layout="wide"
    )
    st.header(league_name)
    st.markdown(
        """Current data for **{league_name}** (Updated **{last_updated}**.)  
**{games_played}** out of **{games_per_season}** games have been played. **{games_remaining}** games remain.  
The season is **{percent_complete}%** comple!""".format(
            league_name=league_name,
            last_updated=datetime.datetime.strftime(
                frames["League Data"].iloc[0]["Last Updated"], "%a %b %d %Y at %I:%M %p"
            ),
            games_played=frames["League Data"].iloc[0]["Games Played (Total)"],
            games_remaining=games_remaining,
            games_per_season=frames["League Data"].iloc[0]["Games per Season"],
            percent_complete=round(
                frames["League Data"].iloc[0]["% of Games Completed"] * 100, 2
            ),
        )
    )

    # If the season is complete, let's party!
    if games_remaining == 0:
        with st.container(
            horizontal=True, horizontal_alignment="left", vertical_alignment="center"
        ):
            st.text("This season is complete!")
            if st.button(
                "Let's celebrate!",
                icon="🔥",
            ):
                st.balloons()

    regular_season, bowls, postseason, awards = st.tabs(
        ["Regular Season", "Bowls", "Postseason", "Awards"],
    )

    with regular_season:

        st.caption(f"Regular season statistics for {league_name}")

        match_summaries, match_performances, trainer_standings, trainer_pokemon = (
            st.tabs(
                [
                    "Match Summaries",
                    "Match Performances",
                    "Trainer Standings",
                    "Trainer Pokémon",
                ]
            )
        )

        with match_summaries:

            match_summaries_df = frames["(RS) Match Summaries"]
            build_schedule_tab(match_summaries_df, style="Tab")

        with match_performances:

            match_performances_df = frames["(RS) Match Performances"]

            st.dataframe(
                match_performances_df,
                hide_index=True,
            )

        with trainer_standings:

            trainer_summaries_df = frames["(RS) Trainer Summaries"]
            divisions = list(trainer_summaries_df["Division"].unique())

            by_division, all_players = st.tabs(["By Division", "All Trainers"])

            with by_division:
                for division in divisions:
                    st.subheader(division)
                    st.dataframe(
                        trainer_summaries_df.loc[
                            trainer_summaries_df["Division"] == division
                        ],
                        height="content",
                        hide_index=True,
                    )

            with all_players:
                st.subheader("Summaries for all trainers")
                st.dataframe(trainer_summaries_df, height="content", hide_index=True)

        with trainer_pokemon:

            trainer_pokemon_df = frames["(RS) Trainer Pokémon"]

            st.dataframe(trainer_pokemon_df, hide_index=True)

    with bowls:

        st.caption(f"Bowl game statistics for {league_name}")

        bowl_summaries, bowl_performances = st.tabs(
            [
                "Bowl Game Summaries",
                "Bowl Game Performances",
            ]
        )

        with bowl_summaries:

            bowl_summaries_df = frames["(BOWL) Game Summaries"]
            build_schedule_tab(bowl_summaries_df, "Bowl Games", "Bowl Game", False)

        with bowl_performances:

            bowl_performances_df = frames["(BOWL) Game Performances"]

            st.dataframe(
                bowl_performances_df,
                height="content",
                hide_index=True,
            )

    with postseason:

        st.caption(f"Postseason statistics for {league_name}")

        match_summaries, match_performances, trainer_pokemon = st.tabs(
            [
                "Match Summaries",
                "Match Performances",
                "Trainer Pokémon",
            ]
        )

        with match_summaries:

            match_summaries_df = frames["(PS) Match Summaries"]
            build_schedule_tab(match_summaries_df, style="Tab")

        with match_performances:

            match_performances_df = frames["(PS) Match Performances"]

            st.dataframe(
                match_performances_df,
                hide_index=True,
            )

        with trainer_pokemon:

            trainer_pokemon_df = frames["(PS) Trainer Pokémon"]

            st.dataframe(trainer_pokemon_df, hide_index=True)

    with awards:

        st.text(f"Awards data for {league_name}")

        awards_df = frames["Awards"]
        st.dataframe(awards_df, height="content", hide_index=True)


def build_website(input_data: list[dict[str, pd.DataFrame]]):

    st.logo("static/flamigo.png", size="large")

    pages: dict[str, list[st.Page]] = {"Info": [], "Seasons": []}

    pages["Info"].append(st.Page(landing, title="About", url_path="About"))

    for frames in input_data:
        league_name = frames["League Data"].iloc[0]["League Name"]
        pages["Seasons"].append(
            st.Page(lambda: build_page(frames), title=league_name, url_path=league_name)
        )

    return st.navigation(pages)


if __name__ == "__main__":

    inputs = read_input_xlsx_files()
    pg = build_website(inputs)
    pg.run()
