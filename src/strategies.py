import time
from random import shuffle
import random
from src.piece import Piece
from src.move_not_possible_exception import MoveNotPossibleException
from src.colour import Colour


class Strategy:
    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        raise NotImplemented()

    def game_over(self, opponents_activity):
        pass

class MoveFurthestBackStrategy(Strategy):

    @staticmethod
    def get_difficulty():
        return "Medium"

    def assess_board(self, colour, myboard):
        pieces = myboard.get_pieces(colour)
        pieces_on_board = len(pieces)
        sum_distances = 0
        number_of_singles = 0
        number_occupied_spaces = 0
        sum_single_distance_away_from_home = 0
        sum_distances_to_endzone = 0

        for piece in pieces:
            sum_distances += piece.spaces_to_home()
            if piece.spaces_to_home() > 6:
                sum_distances_to_endzone += piece.spaces_to_home() - 6

        for location in range(1, 25):
            pieces = myboard.pieces_at(location)
            if len(pieces) != 0 and pieces[0].colour == colour:
                if len(pieces) == 1:
                    number_of_singles += 1
                    sum_single_distance_away_from_home += 25 - pieces[0].spaces_to_home()
                elif len(pieces) > 1:
                    number_occupied_spaces += 1

        opponents_taken_pieces = len(myboard.get_taken_pieces(colour.other()))
        opponent_pieces = myboard.get_pieces(colour.other())
        sum_distances_opponent = sum(p.spaces_to_home() for p in opponent_pieces)

        return {
            'number_occupied_spaces': number_occupied_spaces,
            'opponents_taken_pieces': opponents_taken_pieces,
            'sum_distances': sum_distances,
            'sum_distances_opponent': sum_distances_opponent,
            'number_of_singles': number_of_singles,
            'sum_single_distance_away_from_home': sum_single_distance_away_from_home,
            'pieces_on_board': pieces_on_board,
            'sum_distances_to_endzone': sum_distances_to_endzone,
        }

    def is_point_safe(self, board, location, colour):
        opponent_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE
        opponent_pieces = board.get_pieces(opponent_colour)
        return sum(1 for piece in opponent_pieces if piece.location == location) < 2

    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        result = self.move_recursively(board, colour, dice_roll)

        if len(dice_roll) == 2:
            new_dice_roll = dice_roll.copy()
            new_dice_roll.reverse()
            result_swapped = self.move_recursively(board, colour, dice_rolls=new_dice_roll)
            if result_swapped['best_value'] < result['best_value'] and len(result_swapped['best_moves']) >= len(result['best_moves']):
                result = result_swapped

        if len(result['best_moves']) != 0:
            for move in result['best_moves']:
                try:
                    make_move(move['piece_at'], move['die_roll'])
                except:
                    pass

    def move_recursively(self, board, colour, dice_rolls):
        max_depth = 100
        best_board_value = float('inf')
        best_pieces_to_move = []

        if len(dice_rolls) == 0:
            return {'best_value': best_board_value, 'best_moves': []}
        if max_depth <= 0:
            return {'best_value': best_board_value, 'best_moves': []}

        pieces_to_try = list(set(x.location for x in board.get_pieces(colour)))
        valid_pieces = [board.get_piece_at(loc) for loc in pieces_to_try]
        valid_pieces.sort(key=Piece.spaces_to_home, reverse=True)

        dice_rolls_left = dice_rolls.copy()
        die_roll = dice_rolls_left.pop(0)

        for piece in valid_pieces:
            target_location = piece.location + (die_roll if colour == Colour.WHITE else -die_roll)
            if board.is_move_possible(piece, die_roll) and self.is_point_safe(board, target_location, colour):
                board_copy = board.create_copy()
                new_piece = board_copy.get_piece_at(piece.location)
                board_copy.move_piece(new_piece, die_roll)

                if len(dice_rolls_left) > 0:
                    result = self.move_recursively(board_copy, colour, dice_rolls_left)
                    if len(result['best_moves']) == 0:
                        board_value = self.evaluate_board(board_copy, colour)
                        if board_value < best_board_value and len(best_pieces_to_move) < 2:
                            best_board_value = board_value
                            best_pieces_to_move = [{'die_roll': die_roll, 'piece_at': piece.location}]
                    elif result['best_value'] < best_board_value:
                        if len(result['best_moves']) + 1 >= len(best_pieces_to_move):
                            best_board_value = result['best_value']
                            move = {'die_roll': die_roll, 'piece_at': piece.location}
                            best_pieces_to_move = [move] + result['best_moves']
                else:
                    board_value = self.evaluate_board(board_copy, colour)
                    if board_value < best_board_value and len(best_pieces_to_move) < 2:
                        best_board_value = board_value
                        best_pieces_to_move = [{'die_roll': die_roll, 'piece_at': piece.location}]

        return {'best_value': best_board_value, 'best_moves': best_pieces_to_move}

    def evaluate_board(self, myboard, colour):
        board_stats = self.assess_board(colour, myboard)
        return board_stats['sum_distances'] - float(board_stats['sum_distances_opponent']) / 3 + \
               2 * board_stats['number_of_singles'] - \
               board_stats['number_occupied_spaces'] - board_stats['opponents_taken_pieces']


from src.strategies import MoveFurthestBackStrategy

class LookAheadStrategy(MoveFurthestBackStrategy):
    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        next_roll = opponents_activity.get("next_opponent_roll", [])
        opponent_colour = colour.other()
        opponent_targets = set()

        if next_roll:
            for piece in board.get_pieces(opponent_colour):
                for roll in next_roll:
                    dest = board.destination_for(piece, roll)
                    if dest is not None:
                        opponent_targets.add(dest)

        for piece in board.get_pieces(colour):
            for roll in sorted(dice_roll, reverse=True):
                if board.is_move_possible(piece, roll):
                    dest = board.destination_for(piece, roll)
                    if dest in opponent_targets:
                        stack = board.pieces_at(dest)
                        if len(stack) == 0 or (stack[0].colour == colour and len(stack) > 1):
                            try:
                                print(f"[{colour}] blocking opponent by moving to {dest} with roll {roll}")
                                make_move(piece.location, roll)
                                return
                            except Exception as e:
                                print(f"[{colour}] blocking move failed: {e}")

        print(f"[{colour}] no safe blocking move available — falling back to MoveFurthestBackStrategy")
        super().move(board, colour, dice_roll, make_move, opponents_activity)

class HumanStrategy(Strategy):
    def __init__(self, name="Human"):
        self.__name = name

    @staticmethod
    def get_difficulty():
        return "N/A"

    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        print("It is %s's turn, you are %s, your roll is %s" % (self.__name, colour, dice_roll))
        while len(dice_roll) > 0 and not board.has_game_ended():
            board.print_board()
            if board.no_moves_possible(colour, dice_roll):
                print("There are no valid moves. Your turn has ended.")
                time.sleep(3)
                break
            print("You have %s left" % dice_roll)
            location = self.get_location(board, colour)
            piece = board.get_piece_at(location)
            while True:
                try:
                    value = int(input("How far (or 0 to move another piece)?\n"))
                    if value == 0:
                        break                    
                    rolls_moved = make_move(piece.location, value)
                    for roll in rolls_moved:
                        dice_roll.remove(roll)
                    print("")
                    print("")
                    break
                except ValueError:
                    print("That's not a number! Try again")
                except MoveNotPossibleException as e:
                    print(str(e))

        print("Done!")

    def get_location(self, board, colour):
        value = None
        while value is None:
            try:
                location = int(input("Enter the location of the piece you want to move?\n"))
                piece_at_location = board.get_piece_at(location)
                if piece_at_location is None or piece_at_location.colour != colour:
                    print("You don't have a piece at location %s" % location)
                else:
                    value = location
            except ValueError:
                print("That's not a number! Try again")
        return value


class MoveMostlySmart(Strategy):
    def __init__(self, base_strategy: Strategy = None, random_turn_range=(0, 20), game_index: int = None):
        from src.strategies import MoveFurthestBackStrategy
        self.base_strategy = base_strategy if base_strategy else MoveFurthestBackStrategy()
        self.random_strategy = MoveRandomPiece()
        self.random_turn_number = random.randint(*random_turn_range)
        self.turn_counter = 0
        self.random_move_done = False
        self.game_index = game_index

    @staticmethod
    def get_difficulty():
        return "Medium+Random"

    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        self.turn_counter += 1
        if not self.random_move_done and self.turn_counter == self.random_turn_number:
            #print(f"[Game {self.game_index}] Random move triggered on turn {self.turn_counter}")
            self.random_strategy.move(board, colour, dice_roll, make_move, opponents_activity)
            self.random_move_done = True
        else:
            self.base_strategy.move(board, colour, dice_roll, make_move, opponents_activity)


class MoveRandomPiece(Strategy):
    @staticmethod
    def get_difficulty():
        return "Easy"

    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        from random import shuffle
        for die_roll in dice_roll:
            pieces = board.get_pieces(colour)
            shuffle(pieces)
            for piece in pieces:
                if board.is_move_possible(piece, die_roll):
                    try:
                        make_move(piece.location, die_roll)
                        break
                    except:
                        continue
