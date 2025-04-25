import time
from random import randint
from src.colour import Colour
from src.game import Game
from src.strategies import Strategy
from src.strategies import MoveFurthestBackStrategy, MoveMostlySmart
from src.strategies import MoveRandomPiece
from src.experiment import Experiment
from src.strategies import LookAheadStrategy



class Experiment:
    def __init__(self, games_to_play: int, white_strategy_factory, black_strategy_factory):
        self.__games_to_play = games_to_play
        self.__white_strategy_factory = white_strategy_factory
        self.__black_strategy_factory = black_strategy_factory
        self.__white_wins = 0
        self.__black_wins = 0

    def run(self):
        for game_index in range(self.__games_to_play):
            first_player = Colour.WHITE if game_index % 2 == 0 else Colour.BLACK
            game = Game(
                white_strategy=self.__white_strategy_factory(game_index),
                black_strategy=self.__black_strategy_factory(game_index),
                first_player=first_player
            )
            game.run_game(verbose=False)

            if game.who_won() == Colour.WHITE:
                self.__white_wins += 1
            else:
                self.__black_wins += 1



    def print_results(self):
        print(f"After {self.__games_to_play} games")
        print(f"White wins: {self.__white_wins}")
        print(f"Black wins: {self.__black_wins}")


if __name__ == "__main__":
    experiment = Experiment(
        games_to_play=1000,
        white_strategy_factory=lambda game_index: MoveFurthestBackStrategy(),
        black_strategy_factory=lambda game_index: MoveFurthestBackStrategy()
    )
    experiment.run()
    experiment.print_results()

