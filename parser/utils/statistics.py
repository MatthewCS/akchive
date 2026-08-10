class PokemonStats(object):
    name: str
    trainer: str
    direct_kills: int
    passive_kills: int
    deaths: int
    matches_played: int
    uid: str

    def __init__(
        self,
        name: str,
        trainer: str,
        direct_kills: int,
        passive_kills: int,
        deaths: int,
    ):
        self.name = name
        self.trainer = trainer
        self.direct_kills = direct_kills
        self.passive_kills = passive_kills
        self.deaths = deaths
        self.matches_played = 1
        self.uid = f"{trainer}'s partner {name}"

    def merge(self, new_stats):
        if self.name == new_stats.name and self.trainer == new_stats.trainer:
            self.direct_kills += new_stats.direct_kills
            self.passive_kills += new_stats.passive_kills
            self.deaths += new_stats.deaths
            self.matches_played += new_stats.matches_played
        else:
            print("WTF", self, new_stats)
            exit(1)

    def __str__(self):
        return (
            f"{self.name} (trainer: {self.trainer}) has {self.direct_kills} direct kills,"
            + f" {self.passive_kills} passive kills, and {self.deaths} deaths."
        )


class MatchResults(object):
    player_1: str = ""
    player_2: str = ""
    winner: str = ""
    margin_of_victory: int = 0
    player_1_pokemon: list[PokemonStats] = []
    player_2_pokemon: list[PokemonStats] = []
    replay_url: str = ""

    def __init__(self):
        # If I don't do it this way then there's tomfoolery with pointers
        # (Every MatchResults object would share the same pokemon lists)
        # (That would be bad!)
        self.player_1_pokemon = []
        self.player_2_pokemon = []

    def has_trainers(self, trainers: list[str]) -> bool:
        return (
            self.player_1 in trainers
            and self.player_2 in trainers
            and len(trainers) == 2
        )

    def has_pokemon(self, pokemon_name: str) -> bool:

        return (
            len(
                [
                    pkmn
                    for pkmn in self.player_1_pokemon + self.player_2_pokemon
                    if pkmn.name == pokemon_name
                ]
            )
            > 0
        )

    def __str__(self):
        return (
            f"{self.player_1} vs {self.player_2}\n"
            + "\n"
            + f"{self.winner} won by a margin of {self.margin_of_victory} pokemon.\n"
            + "\n"
            + f"{self.player_1}:\n"
            + "\n".join(
                [
                    f"{pokemon.name} had {pokemon.direct_kills} direct kills, {pokemon.passive_kills} passive kills, and {pokemon.deaths} deaths."
                    for pokemon in self.player_1_pokemon
                ]
            )
            + "\n"
            + "\n"
            + f"{self.player_2}:\n"
            + "\n".join(
                [
                    f"{pokemon.name} had {pokemon.direct_kills} direct kills, {pokemon.passive_kills} passive kills, and {pokemon.deaths} deaths."
                    for pokemon in self.player_2_pokemon
                ]
            )
            + "\n"
            + "\n"
            + f"Replay: {self.replay_url}"
        )


class TrainerStats(object):
    name: str
    division: str
    wins: int = 0
    losses: int = 0
    differential: int = 0
    pokemon: dict[str, PokemonStats] = {}
    matches: list[MatchResults] = []

    def __init__(self, name: str, division: str = ""):

        self.name = name
        self.division = division
        self.pokemon = {}
        self.matches = []

    def add_match(self, new_match: MatchResults):

        player = 0
        if new_match.player_1 == self.name:
            player = 1
        elif new_match.player_2 == self.name:
            player = 2
        else:
            raise Exception(f'"{self.name}" not found in the given match:\n{new_match}')

        self.matches.append(new_match)
        # "I hope I win!" -Porygon
        if new_match.winner == self.name:
            self.wins += 1
            self.differential += new_match.margin_of_victory
        else:
            self.losses += 1
            self.differential -= new_match.margin_of_victory

        if player == 1:
            for pokemon in new_match.player_1_pokemon:
                if pokemon.uid not in self.pokemon:
                    self.pokemon[pokemon.uid] = PokemonStats(
                        pokemon.name,
                        pokemon.trainer,
                        pokemon.direct_kills,
                        pokemon.passive_kills,
                        pokemon.deaths,
                    )
                else:
                    self.pokemon[pokemon.uid].merge(pokemon)
        else:
            for pokemon in new_match.player_2_pokemon:
                if pokemon.uid not in self.pokemon:
                    self.pokemon[pokemon.uid] = PokemonStats(
                        pokemon.name,
                        pokemon.trainer,
                        pokemon.direct_kills,
                        pokemon.passive_kills,
                        pokemon.deaths,
                    )
                else:
                    self.pokemon[pokemon.uid].merge(pokemon)

    def __str__(self):

        return (
            f"Name: {self.name}\n\n"
            + f"Record: {self.wins}-{self.losses}\n\n"
            + f"Pokemon:\n{"\n".join([str(pokemon) for pokemon in self.pokemon.values()])}"
        )
