import time
from random import randint
from src.colour import Colour
from src.game import Game
from src.strategies import Strategy
from src.strategies import MoveFurthestBackStrategy
from src.strategies import MoveRandomPiece
from src.experiment import Experiment


class Experiment:
    def __init__(self, games_to_play: int, white_strategy: Strategy, black_strategy: Strategy):
        self.__games_to_play = games_to_play
        self.__white_strategy = white_strategy
        self.__black_strategy = black_strategy
        self.__white_wins = 0
        self.__black_wins = 0

    def run(self):
        # Run 100 games, alternating who goes first
        for game_index in range(self.__games_to_play):
            # Alternate who starts (white starts first, then black, and so on)
            first_player = Colour.WHITE if game_index % 2 == 0 else Colour.BLACK
            game = Game(
                white_strategy=self.__white_strategy,
                black_strategy=self.__black_strategy,
                first_player=first_player
            )
            game.run_game(verbose=False)
            
            # Update win count
            if game.who_won() == Colour.WHITE:
                self.__white_wins += 1
            else:
                self.__black_wins += 1

    def print_results(self):
        print(f"After {self.__games_to_play} games")
        print(f"White wins: {self.__white_wins}")
        print(f"Black wins: {self.__black_wins}")


if __name__ == "__main__":
    # Create strategies for both players
    white_strategy = MoveFurthestBackStrategy()
    black_strategy = MoveFurthestBackStrategy()  # Replace with any strategy you'd like

    # Create and run the experiment for 100 games
    experiment = Experiment(games_to_play=10000, white_strategy=white_strategy, black_strategy=black_strategy)
    experiment.run()

    # Print the results of the experiment
    experiment.print_results()