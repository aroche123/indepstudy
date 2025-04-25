from random import shuffle
import copy
import json

from src.colour import Colour
from src.piece import Piece


class Board:
    def __init__(self):
        self.__pieces = []

    @classmethod
    def create_starting_board(cls):
        board = Board()
        board.add_many_pieces(2, Colour.WHITE, 1)
        board.add_many_pieces(5, Colour.BLACK, 6)
        board.add_many_pieces(3, Colour.BLACK, 8)
        board.add_many_pieces(5, Colour.WHITE, 12)
        board.add_many_pieces(5, Colour.BLACK, 13)
        board.add_many_pieces(3, Colour.WHITE, 17)
        board.add_many_pieces(5, Colour.WHITE, 19)
        board.add_many_pieces(2, Colour.BLACK, 24)
        return board

    def add_many_pieces(self, number_of_pieces, colour, location):
        for _ in range(number_of_pieces):
            self.__pieces.append(Piece(colour, location))

    def is_move_possible(self, piece, die_roll):
        if len(self.pieces_at(self.__taken_location(piece.colour))) > 0:
            if piece.location != self.__taken_location(piece.colour):
                return False
        if piece.colour == Colour.BLACK:
            die_roll = -die_roll
        new_location = piece.location + die_roll
        if new_location <= 0 or new_location >= 25:
            if not self.can_move_off(piece.colour):
                return False
            if new_location != 0 and new_location != 25:
                return not any(x.spaces_to_home() >= abs(die_roll) for x in self.get_pieces(piece.colour))
            return True
        pieces_at_new_location = self.pieces_at(new_location)
        if len(pieces_at_new_location) == 0 or len(pieces_at_new_location) == 1:
            return True
        return self.pieces_at(new_location)[0].colour == piece.colour

    def no_moves_possible(self, colour, dice_roll):
        piece_locations = list(set(x.location for x in self.get_pieces(colour)))
        dice_roll = list(set(dice_roll))
        pieces = [self.get_piece_at(loc) for loc in piece_locations]
        return not any(self.is_move_possible(piece, die) for die in dice_roll for piece in pieces)

    def can_move_off(self, colour):
        return all(x.spaces_to_home() <= 6 for x in self.get_pieces(colour))

    def move_piece(self, piece, die_roll):
        if piece not in self.__pieces:
            raise Exception('This piece does not belong to this board')
        if not self.is_move_possible(piece, die_roll):
            raise Exception('You cannot make this move')
        if piece.colour == Colour.BLACK:
            die_roll = -die_roll

        new_location = piece.location + die_roll
        if new_location <= 0 or new_location >= 25:
            self.__remove_piece(piece)
        else:
            pieces_at_new_location = self.pieces_at(new_location)
            if len(pieces_at_new_location) == 1 and pieces_at_new_location[0].colour != piece.colour:
                pieces_at_new_location[0].location = self.__taken_location(pieces_at_new_location[0].colour)
            piece.location = new_location

        return new_location

    def destination_for(self, piece, die_roll):
        if not self.is_move_possible(piece, die_roll):
            return None
        if piece.colour == Colour.BLACK:
            die_roll = -die_roll
        return piece.location + die_roll

    def can_land_on(self, colour, location):
        pieces = self.pieces_at(location)
        if len(pieces) == 0:
            return True
        if len(pieces) == 1 and pieces[0].colour != colour:
            return True
        return pieces[0].colour == colour

    def pieces_at(self, location):
        return [x for x in self.__pieces if x.location == location]

    def get_piece_at(self, location):
        pieces = self.pieces_at(location)
        return pieces[0] if pieces else None

    def get_pieces(self, colour):
        pieces = [x for x in self.__pieces if x.colour == colour]
        shuffle(pieces)
        return pieces

    def get_taken_pieces(self, colour):
        return self.pieces_at(self.__taken_location(colour))

    def has_game_ended(self):
        return len(self.get_pieces(Colour.WHITE)) == 0 or len(self.get_pieces(Colour.BLACK)) == 0

    def who_won(self):
        if not self.has_game_ended():
            raise Exception('The game has not finished yet!')
        return Colour.WHITE if len(self.get_pieces(Colour.WHITE)) == 0 else Colour.BLACK

    def create_copy(self):
        return copy.deepcopy(self)

    def get_move_lambda(self):
        return lambda l, r: self.move_piece(self.get_piece_at(l), r)

    def print_board(self):
        print("  13                  18   19                  24   25")
        print("---------------------------------------------------")
        line = "|"
        for i in range(13, 19):
            line += self.__pieces_at_text(i)
        line += "|"
        for i in range(19, 25):
            line += self.__pieces_at_text(i)
        line += "|" + self.__pieces_at_text(self.__taken_location(Colour.BLACK))
        print(line)
        for _ in range(3):
            print("|                        |                        |")
        line = "|"
        for i in reversed(range(7, 13)):
            line += self.__pieces_at_text(i)
        line += "|"
        for i in reversed(range(1, 7)):
            line += self.__pieces_at_text(i)
        line += "|" + self.__pieces_at_text(self.__taken_location(Colour.WHITE))
        print(line)
        print("---------------------------------------------------")
        print("  12                  7    6                   1    0")

    def to_json(self):
        data = {}
        for location in range(26):
            pieces = self.pieces_at(location)
            if pieces:
                data[location] = {'colour': pieces[0].colour.__str__(), 'count': len(pieces)}
        return json.dumps(data)

    def __taken_location(self, colour):
        return 0 if colour == Colour.WHITE else 25

    def __pieces_at_text(self, location):
        pieces = self.pieces_at(location)
        if not pieces:
            return " .  "
        return f" {len(pieces)}{'W' if pieces[0].colour == Colour.WHITE else 'B'} "

    def __remove_piece(self, piece):
        self.__pieces.remove(piece)
