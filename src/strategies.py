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

    #method will assess board for the color and returns dictionary of statistics
    def assess_board(self, colour, myboard):
        #gets all the pieces
        pieces = myboard.get_pieces(colour)
        pieces_on_board = len(pieces)

        #vars for board statistics
        sum_distances = 0
        number_of_singles = 0
        number_occupied_spaces = 0
        sum_single_distance_away_from_home = 0
        sum_distances_to_endzone = 0

        #total distance of pieces from home
        for piece in pieces:
            sum_distances += piece.spaces_to_home()
            if piece.spaces_to_home() > 6:
                sum_distances_to_endzone += piece.spaces_to_home() - 6

        #looks for occupied spaces and singles 
        for location in range(1, 25):
            pieces = myboard.pieces_at(location)
            if len(pieces) != 0 and pieces[0].colour == colour:
                if len(pieces) == 1:
                    number_of_singles += 1
                    sum_single_distance_away_from_home += 25 - pieces[0].spaces_to_home()
                elif len(pieces) > 1:
                    number_occupied_spaces += 1

        #evaluates oppponents taken pieces and total distance 
        opponents_taken_pieces = len(myboard.get_taken_pieces(colour.other()))
        opponent_pieces = myboard.get_pieces(colour.other())
        sum_distances_opponent = 0
        for piece in opponent_pieces:
            sum_distances_opponent += piece.spaces_to_home()

        #returns statistics
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

    #checks if place is safe from opponent
    #"safe" if less than 2 pieces there
    def is_point_safe(self, board, location, colour):
        opponent_colour = Colour.BLACK if colour == Colour.WHITE else Colour.WHITE
        opponent_pieces = board.get_pieces(opponent_colour)
        return sum(1 for piece in opponent_pieces if piece.location == location) < 2


    #where we make a move, calculates best move w recursion
    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        result = self.move_recursively(board, colour, dice_roll)

        #if not doubles, try other direction of dice roll
        not_a_double = len(dice_roll) == 2
        if not_a_double:
            new_dice_roll = dice_roll.copy()
            new_dice_roll.reverse()
            result_swapped = self.move_recursively(board, colour, dice_rolls=new_dice_roll)
            #if swapped is better, use that instead 
            if result_swapped['best_value'] < result['best_value'] and len(result_swapped['best_moves']) >= len(result['best_moves']):
                result = result_swapped

        #if best moves found, use them
        if len(result['best_moves']) != 0:
            for move in result['best_moves']:
                make_move(move['piece_at'], move['die_roll'])


    #recursive method to calculate best move 
    def move_recursively(self, board, colour, dice_rolls):
        # Prevent infinite recursion by setting a max recursion depth (e.g., 100).
        max_depth = 100
        best_board_value = float('inf')
        best_pieces_to_move = []

        # No more dice rolls left, so stop recursion
        if len(dice_rolls) == 0:
            return {'best_value': best_board_value, 'best_moves': []} 

        # avoid infinite loops
        if max_depth <= 0:
            return {'best_value': best_board_value, 'best_moves': []}

        #all pieces on board for player
        pieces_to_try = [x.location for x in board.get_pieces(colour)]
        pieces_to_try = list(set(pieces_to_try))

        #valid pieces to move, sorted by distance from home
        valid_pieces = []
        for piece_location in pieces_to_try:
            valid_pieces.append(board.get_piece_at(piece_location))
        valid_pieces.sort(key=Piece.spaces_to_home, reverse=True)

        #copy for more recursion
        dice_rolls_left = dice_rolls.copy()
        die_roll = dice_rolls_left.pop(0)

        #move valid piece w current
        for piece in valid_pieces:
            target_location = piece.location + (die_roll if colour == Colour.WHITE else -die_roll)

            #see if move is possible and target location safe
            if board.is_move_possible(piece, die_roll) and self.is_point_safe(board, target_location, colour):
                board_copy = board.create_copy()
                new_piece = board_copy.get_piece_at(piece.location)
                board_copy.move_piece(new_piece, die_roll)

                #if any dice left,more  recursion 
                if len(dice_rolls_left) > 0:
                    result = self.move_recursively(board_copy, colour, dice_rolls_left)
                    if len(result['best_moves']) == 0:
                        board_value = self.evaluate_board(board_copy, colour)
                        if board_value < best_board_value and len(best_pieces_to_move) < 2:
                            best_board_value = board_value
                            best_pieces_to_move = [{'die_roll': die_roll, 'piece_at': piece.location}]
                    elif result['best_value'] < best_board_value:
                        new_best_moves_length = len(result['best_moves']) + 1
                        if new_best_moves_length >= len(best_pieces_to_move):
                            best_board_value = result['best_value']
                            move = {'die_roll': die_roll, 'piece_at': piece.location}
                            best_pieces_to_move = [move] + result['best_moves']
                else:
                    board_value = self.evaluate_board(board_copy, colour)
                    if board_value < best_board_value and len(best_pieces_to_move) < 2:
                        best_board_value = board_value
                        best_pieces_to_move = [{'die_roll': die_roll, 'piece_at': piece.location}]

        return {'best_value': best_board_value,
                'best_moves': best_pieces_to_move}


    #evaluate board's val based on various statistics 
    def evaluate_board(self, myboard, colour):
        board_stats = self.assess_board(colour, myboard)

        #calculate board val considering piece distances, single pieces, oponents taken pieces
        board_value = board_stats['sum_distances'] - float(board_stats['sum_distances_opponent']) / 3 + \
                      2 * board_stats['number_of_singles'] - \
                      board_stats['number_occupied_spaces'] - board_stats['opponents_taken_pieces']
        return board_value


class HumanStrategy(Strategy):
    def __init__(self, name):
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
                    print("You don't have a piece at location %s" % value)
                else:
                    value = location
            except ValueError:
                print("That's not a number! Try again")
        return value


class MoveRandomPiece(Strategy):

    @staticmethod
    def get_difficulty():
        return "Easy"

    def move(self, board, colour, dice_roll, make_move, opponents_activity):
        for die_roll in dice_roll:
            valid_pieces = board.get_pieces(colour)
            shuffle(valid_pieces)
            for piece in valid_pieces:
                if board.is_move_possible(piece, die_roll):
                    make_move(piece.location, die_roll)
                    break

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