import json
import random
import time
from ship import Ship


class Player:
    FLEET = [
        ("Aircraft carrier", "A", 5),
        ("Battleship", "B", 4),
        ("Cruiser", "C", 3),
        ("Submarine", "S", 3),
        ("Destroyer", "D", 2),
    ]

    def __init__(self, name, plan_board, attack_board, difficulty="medium", ships_list=None):
        self.__name = name
        self.__plan_board = plan_board
        self.__attack_board = attack_board
        self.__difficulty = difficulty
        if ships_list is None:
            self.__ships_list = [Ship(name, symbol, size) for name, symbol, size in self.FLEET]
        else:
            self.__ships_list = ships_list

        self._target_queue = []
        self._tried_targets = set()
        self._recent_hits = []
        self._known_direction = None

    def get_player_name(self):
        return self.__name

    def get_ships_list(self):
        return self.__ships_list

    def get_plan_board(self):
        return self.__plan_board

    def get_attack_board(self):
        return self.__attack_board

    def get_difficulty(self):
        return self.__difficulty
    
    def set_difficulty(self, difficulty):
        self.__difficulty = difficulty

    def has_lost_game(self):
        for ship in self.__ships_list:
            if not ship.is_sunk():
                return False
        return True

    def clear_ship_positions(self):
        self.__plan_board.clear_ships()
        for ship in self.__ships_list:
            ship.clear_cells()

    def show_boards(self):
        print(f"\n{self.__name} - Planning Board")
        self.__plan_board.show_board_planning()
        print(f"\n{self.__name} - Attack Board")
        self.__attack_board.show_board_attack(easy_reveal=self.__difficulty == "easy")
        print()

    def show_boards_horizontally(self):
        self.show_boards()

    def position_ships_randomly(self):
        self.clear_ship_positions()
        idx = 0
        while idx < len(self.__ships_list):
            ship = self.__ships_list[idx]
            row = random.randint(0, self.__plan_board.get_num_rows() - 1)
            col = random.randint(0, self.__plan_board.get_num_cols() - 1)
            orient = random.choice(["Horizontal", "Vertical"])
            if self.__plan_board.place_ship(ship, row, col, orient):
                idx += 1

    def position_ships_manually(self):
        self.clear_ship_positions()
        print(f"\n{self.__name} place your ships on the planning board.")
        print("Use coordinates like A0, B3, J9")
        print("Orientation must be H or V")
        for ship in self.__ships_list:
            placed = False
            while not placed:
                self.__plan_board.show_board_planning()
                print(f"Place {ship.get_name()} ({ship.get_letter()}, size {ship.get_size()})")
                coord = input("Start coordinate: ").strip().upper()
                orient_text = input("Orientation (H/V): ").strip().upper()
                parsed = self._parse_coord(coord)
                if parsed is None:
                    print("Invalid coordinate. Try again.\n")
                    continue
                if orient_text not in ("H", "V"):
                    print("Orientation must be H or V.\n")
                    continue
                row, col = parsed
                orient = "Horizontal" if orient_text == "H" else "Vertical"
                if self.__plan_board.place_ship(ship, row, col, orient):
                    placed = True
                else:
                    print("Invalid placement. Ships must stay inside the grid and cannot overlap.\n")

    def _parse_coord(self, coord_text):
        if len(coord_text) < 2:
            return None
        col_letter = coord_text[0].upper()
        col = ord(col_letter) - 65
        if col < 0 or col >= self.__plan_board.get_num_cols():
            return None
        try:
            row = int(coord_text[1:])
        except ValueError:
            return None
        if row < 0 or row >= self.__plan_board.get_num_rows():
            return None
        return row, col

    def to_state(self):
        return {
            "name": self.__name,
            "difficulty": self.__difficulty,
            "ships": [
                {"name": s.get_name(), "symbol": s.get_symbol(), "size": s.get_size()} for s in self.__ships_list
            ],
        }


class HumanPlayer(Player):
    def __init__(self, name, plan_board, attack_board, difficulty="medium"):
        super().__init__(name, plan_board, attack_board, difficulty=difficulty)

    def play(self):
        started = time.time()
        reminder_shown = False
        while True:
            if not reminder_shown and time.time() - started > 5:
                print("You're really taking your time...")
                reminder_shown = True
            input_str = input("Choose cell to attack (e.g. A3): ").strip().upper()
            parsed = self._parse_coord(input_str)
            if input_str == "SAVE":
                return False, {"save_requested": True}
            # ----------------------

            parsed = self._parse_coord(input_str)

            if parsed is None:
                print("Input should be a letter A-J followed by a number 0-9")
                continue
            row, col = parsed
            board = self.get_attack_board()
            if board.was_already_targeted(row, col):
                print("That cell has already been attacked. Try again.")
                continue
            result = board.attack_cell(row, col)
            if result["hit"]:
                if result["sunk"]:
                    print(f"Hit! {result['ship_name']} has been sunk!")
                else:
                    print(f"Hit! {result['ship_name']} was damaged.")
                return True, result
            print("Miss!")
            return False, result


class ComputerPlayer(Player):
    def __init__(self, name, plan_board, attack_board, difficulty="medium", buttons_2d_list=None):
        super().__init__(name, plan_board, attack_board, difficulty=difficulty)
        self.buttons_2d_list = buttons_2d_list or []

    def play(self):
        if self.buttons_2d_list:
            return self.__play_gui()
        print(f"{self.get_player_name()} is thinking...")
        time.sleep(2)
        row, col = self.__pick_target()
        board = self.get_attack_board()
        result = board.attack_cell(row, col)
        self._tried_targets.add((row, col))
        label = f"{chr(65 + col)}{row}"
        if result["hit"]:
            self.__register_hit(row, col, result)
            if result["sunk"]:
                print(f"Computer attacked {label} - {result['ship_name']} has been sunk!")
            else:
                print(f"Computer attacked {label} - Hit!")
            return True, {**result, "row": row, "col": col}
        print(f"Computer attacked {label} - Miss!")
        return False, {**result, "row": row, "col": col}

    def __pick_target(self):
        difficulty = self.get_difficulty()
        if difficulty == "easy":
            return self.__pick_random_target()
        if difficulty == "medium":
            return self.__pick_medium_target()
        return self.__pick_hard_target()

    def __pick_random_target(self):
        board = self.get_attack_board()
        while True:
            row = random.randint(0, board.get_num_rows() - 1)
            col = random.randint(0, board.get_num_cols() - 1)
            if (row, col) not in self._tried_targets and not board.was_already_targeted(row, col):
                return row, col

    def __pick_medium_target(self):
        board = self.get_attack_board()
        while self._target_queue:
            row, col = self._target_queue.pop(0)
            if (row, col) not in self._tried_targets and not board.was_already_targeted(row, col):
                return row, col
        return self.__pick_random_target()

    def __pick_hard_target(self):
        board = self.get_attack_board()
        # Keep following confirmed direction if possible.
        while self._target_queue:
            row, col = self._target_queue.pop(0)
            if (row, col) not in self._tried_targets and not board.was_already_targeted(row, col):
                return row, col

        remaining_sizes = board.get_remaining_ship_sizes()
        if not remaining_sizes:
            return self.__pick_random_target()

        best_score = -1
        best_cells = []
        for r in range(board.get_num_rows()):
            for c in range(board.get_num_cols()):
                if board.was_already_targeted(r, c):
                    continue
                score = self.__placement_score(r, c, remaining_sizes)
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))
        if best_cells:
            return random.choice(best_cells)
        return self.__pick_random_target()

    def __placement_score(self, row, col, remaining_sizes):
        board = self.get_attack_board()
        total = 0
        for size in remaining_sizes:
            # horizontal windows
            for start in range(col - size + 1, col + 1):
                if start < 0 or start + size > board.get_num_cols():
                    continue
                ok = True
                for cc in range(start, start + size):
                    if board.was_already_targeted(row, cc) and not board.cell_has_hit_ship(row, cc):
                        ok = False
                        break
                if ok:
                    total += 1
            # vertical windows
            for start in range(row - size + 1, row + 1):
                if start < 0 or start + size > board.get_num_rows():
                    continue
                ok = True
                for rr in range(start, start + size):
                    if board.was_already_targeted(rr, col) and not board.cell_has_hit_ship(rr, col):
                        ok = False
                        break
                if ok:
                    total += 1
        if (row + col) % 2 == 0:
            total += 1
        return total

    def __register_hit(self, row, col, result):
        if result["sunk"]:
            self._recent_hits.clear()
            self._known_direction = None
            self._target_queue.clear()
            return

        self._recent_hits.append((row, col))
        if len(self._recent_hits) >= 2:
            a = self._recent_hits[-2]
            b = self._recent_hits[-1]
            if a[0] == b[0]:
                self._known_direction = "H"
            elif a[1] == b[1]:
                self._known_direction = "V"

        if self.get_difficulty() == "easy":
            return

        board = self.get_attack_board()
        if self._known_direction == "H":
            same_row = [p for p in self._recent_hits if p[0] == row]
            cols = sorted(c for _, c in same_row)
            left = (row, cols[0] - 1)
            right = (row, cols[-1] + 1)
            for target in (left, right):
                rr, cc = target
                if 0 <= rr < board.get_num_rows() and 0 <= cc < board.get_num_cols():
                    if target not in self._tried_targets and target not in self._target_queue:
                        self._target_queue.append(target)
            return

        if self._known_direction == "V":
            same_col = [p for p in self._recent_hits if p[1] == col]
            rows = sorted(r for r, _ in same_col)
            up = (rows[0] - 1, col)
            down = (rows[-1] + 1, col)
            for target in (up, down):
                rr, cc = target
                if 0 <= rr < board.get_num_rows() and 0 <= cc < board.get_num_cols():
                    if target not in self._tried_targets and target not in self._target_queue:
                        self._target_queue.append(target)
            return

        # No confirmed direction yet: try adjacent cells.
        candidates = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
        for rr, cc in candidates:
            if 0 <= rr < board.get_num_rows() and 0 <= cc < board.get_num_cols():
                if (rr, cc) not in self._tried_targets and (rr, cc) not in self._target_queue:
                    self._target_queue.append((rr, cc))

    def __play_gui(self):
        time.sleep(2)
        while True:
            row, col = self.__pick_target()
            if 0 <= row < len(self.buttons_2d_list) and 0 <= col < len(self.buttons_2d_list[row]):
                button = self.buttons_2d_list[row][col]
                if str(button.cget("state")) != "disabled":
                    button.invoke()
                    return None
