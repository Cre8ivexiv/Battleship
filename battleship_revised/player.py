from ship import Ship
import random
import time

class Player:
    
    def __init__(self, name, plan_board, attack_board, ships_list = []):
        self.__name = name
        self.__plan_board = plan_board
        self.__attack_board = attack_board
        self.__ships_list = []
        if len(ships_list) == 0:
            # Custom 1-5 fleet requested by user. Distinct initials.
            self.__ships_list.append(Ship("Carrier", 5))
            self.__ships_list.append(Ship("Battleship", 4))
            self.__ships_list.append(Ship("Submarine", 3))
            self.__ships_list.append(Ship("Patrol", 2))
            self.__ships_list.append(Ship("Kayak", 1))
        else:
            self.__ships_list = ships_list
        self._target_queue = []
        self._tried_targets = set()
        
    def get_player_name(self):
        return self.__name
    
    def get_ships_list(self):
        return self.__ships_list
    
    def has_lost_game(self):
        for ship in self.__ships_list:
            if not ship.is_sunk():
                return False
        return True
    
    def _get_plan_board(self):
        return self.__plan_board
    
    def get_attack_board(self):
        return self.__attack_board

    def _parse_coord(self, input_str):
        if len(input_str) < 2:
            return None
        col_letter = input_str[0].upper()
        if not ('A' <= col_letter <= chr(64 + self.__plan_board.get_num_cols())):
            return None
        try:
            row = int(input_str[1:])
        except ValueError:
            return None
        col = ord(col_letter) - 65
        if row < 0 or row >= self.__plan_board.get_num_rows():
            return None
        return row, col
    
    def show_boards(self):
        print("\n{} - Planning Board".format(self.__name))
        self.__plan_board.show_board_planning()
        print("\n{} - Attack Board".format(self.__name))
        self.__attack_board.show_board_attack()
    
    def show_boards_horizontally(self):
        self.show_boards()
    
    def position_ships_randomly(self):
        ships_list = self.get_ships_list()
        ship_idx = 0
        while ship_idx < len(ships_list):
            ship = ships_list[ship_idx]
            row = random.randint(0, self._get_plan_board().get_num_rows() - 1)
            col = random.randint(0, self._get_plan_board().get_num_cols() - 1)
            orients = ["Horizontal", "Vertical"]
            orient = orients[random.randint(0, 1)]
            if self._get_plan_board().place_ship(ship, row, col, orient):
                ship_idx += 1

    def position_ships_manually(self):
        print("\n{} place your ships on the planning board.".format(self.__name))
        print("Use format A0, B3, J9 and orientation H or V.")
        for ship in self.get_ships_list():
            placed = False
            while not placed:
                self._get_plan_board().show_board_planning()
                print("Place {} (size {})".format(ship.get_name(), ship.get_size()))
                coord = input("Start coordinate: ").strip()
                orient_in = input("Orientation (H/V): ").strip().upper()
                parsed = self._parse_coord(coord)
                if parsed is None:
                    print("Invalid coordinate. Try again.")
                    continue
                if orient_in not in ("H", "V"):
                    print("Orientation must be H or V.")
                    continue
                row, col = parsed
                orient = "Horizontal" if orient_in == "H" else "Vertical"
                if self._get_plan_board().place_ship(ship, row, col, orient):
                    placed = True
                else:
                    print("Ship cannot be placed there. It must stay in the grid and not overlap.")


class HumanPlayer(Player):
    
    def __init__(self, name, plan_board, attack_board):
        Player.__init__(self, name, plan_board, attack_board)
    
    def play(self):
        while True:
            input_str = input("Choose cell to attack (e.g., A3): ").strip()
            parsed = self._parse_coord(input_str)
            if parsed is None:
                print("Input coordinates should be a letter A-J followed by a number 0-9")
                continue
            row, col = parsed
            attack_board = self.get_attack_board()
            if not attack_board.is_space_free(row, col):
                print("That cell has already been attacked. Try again.")
                continue
            attack_board.attack_cell(row, col)
            if attack_board.cell_has_hit_ship(row, col):
                message = attack_board.get_cell_hit_ship_status(row, col)
                print("It's a hit! {}".format(message))
                return True
            print("Miss!")
            return False


class ComputerPlayer(Player):
    
    def __init__(self, name, plan_board, attack_board, buttons_2d_list = []):
        Player.__init__(self, name, plan_board, attack_board)
        self.buttons_2d_list = buttons_2d_list
    
    def play(self):
        if len(self.buttons_2d_list) > 0:
            return self.__play_gui()
        print("Computer player's turn")
        time.sleep(1)
        attack_board = self.get_attack_board()
        while True:
            row, col = self.__get_target_coords(attack_board)
            if attack_board.is_space_free(row, col):
                attack_board.attack_cell(row, col)
                self._tried_targets.add((row, col))
                col_letter = chr(65 + col)
                if attack_board.cell_has_hit_ship(row, col):
                    self.__queue_adjacent_targets(row, col, attack_board)
                    message = attack_board.get_cell_hit_ship_status(row, col)
                    print("Computer attacked {}{} - Hit! {}".format(col_letter, row, message))
                    return True
                print("Computer attacked {}{} - Miss!".format(col_letter, row))
                return False
    
    def __get_target_coords(self, attack_board):
        while self._target_queue:
            row, col = self._target_queue.pop(0)
            if (row, col) not in self._tried_targets and attack_board.is_space_free(row, col):
                return row, col
        return (
            random.randint(0, attack_board.get_num_rows() - 1),
            random.randint(0, attack_board.get_num_cols() - 1)
        )

    def __queue_adjacent_targets(self, row, col, attack_board):
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        for nr, nc in candidates:
            if 0 <= nr < attack_board.get_num_rows() and 0 <= nc < attack_board.get_num_cols():
                if (nr, nc) not in self._tried_targets and (nr, nc) not in self._target_queue:
                    self._target_queue.append((nr, nc))
    
    def __play_gui(self):
        time.sleep(1)
        while True:
            row = random.randint(0, len(self.buttons_2d_list) - 1)
            col = random.randint(0, len(self.buttons_2d_list[row]) - 1)
            button = self.buttons_2d_list[row][col]
            if str(button.cget("state")) != "disabled":
                button.invoke()
                return None
