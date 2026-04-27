import json
from cell import Cell


class GameBoard:
    RED = "\033[31m"
    WHITE = "\033[97m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    def __init__(self, num_rows=10, num_cols=10):
        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__board = []
        for i in range(self.__num_rows):
            row = []
            for j in range(self.__num_cols):
                row.append(Cell(i, j))
            self.__board.append(row)

    def get_num_rows(self):
        return self.__num_rows

    def get_num_cols(self):
        return self.__num_cols

    def get_cell(self, row, col):
        return self.__board[row][col]

    def clear_ships(self):
        for i in range(self.__num_rows):
            for j in range(self.__num_cols):
                self.__board[i][j].set_ship(None)
                self.__board[i][j].set_hit(False)

    def is_space_free(self, row, col):
        if row < 0 or row >= self.__num_rows or col < 0 or col >= self.__num_cols:
            return False
        return not self.__board[row][col].is_hit()

    def was_already_targeted(self, row, col):
        if row < 0 or row >= self.__num_rows or col < 0 or col >= self.__num_cols:
            return False
        return self.__board[row][col].is_hit()

    def attack_cell(self, row, col):
        cell = self.__board[row][col]
        cell.set_hit(True)
        result = {
            "hit": cell.has_ship(),
            "miss": not cell.has_ship(),
            "ship_name": None,
            "ship_symbol": None,
            "sunk": False,
            "sunk_cells": [],
        }
        if cell.has_ship():
            ship = cell.get_ship()
            result["ship_name"] = ship.get_name()
            result["ship_symbol"] = ship.get_letter()
            result["sunk"] = ship.is_sunk()
            if result["sunk"]:
                result["sunk_cells"] = [c.get_coords() for c in ship.get_cells_list()]
        return result

    def cell_has_hit_ship(self, row, col):
        cell = self.__board[row][col]
        return cell.is_hit() and cell.has_ship()

    def get_cell_hit_ship_name(self, row, col):
        if self.cell_has_hit_ship(row, col):
            return self.__board[row][col].get_ship().get_name()
        return None

    def get_cell_hit_ship_status(self, row, col):
        if not self.cell_has_hit_ship(row, col):
            return None
        ship = self.__board[row][col].get_ship()
        if ship.is_sunk():
            return f"{ship.get_name()} has been sunk!"
        hits = 0
        for cell in ship.get_cells_list():
            if cell.is_hit():
                hits += 1
        return f"{ship.get_name()} has been hit {hits} time(s)."

    def place_ship(self, ship, row, col, orient="Horizontal"):
        if orient == "Horizontal":
            return self.__place_ship_horizontally(ship, row, col)
        if orient == "Vertical":
            return self.__place_ship_vertically(ship, row, col)
        return False

    def __fit_horizontal_start(self, ship, start_col):
        if start_col + ship.get_size() > self.__num_cols:
            start_col = self.__num_cols - ship.get_size()
        return max(0, start_col)

    def __fit_vertical_start(self, ship, start_row):
        if start_row + ship.get_size() > self.__num_rows:
            start_row = self.__num_rows - ship.get_size()
        return max(0, start_row)

    def __place_ship_horizontally(self, ship, row, start_col):
        start_col = self.__fit_horizontal_start(ship, start_col)
        if not self.__can_ship_fit_horizontally(ship, row, start_col):
            return False
        ship.clear_cells()
        for col in range(start_col, start_col + ship.get_size()):
            self.__board[row][col].set_ship(ship)
            ship.add_cell(self.__board[row][col])
        return True

    def __place_ship_vertically(self, ship, start_row, col):
        start_row = self.__fit_vertical_start(ship, start_row)
        if not self.__can_ship_fit_vertically(ship, start_row, col):
            return False
        ship.clear_cells()
        for row in range(start_row, start_row + ship.get_size()):
            self.__board[row][col].set_ship(ship)
            ship.add_cell(self.__board[row][col])
        return True

    def __can_ship_fit_horizontally(self, ship, row, start_col):
        if row < 0 or row >= self.__num_rows:
            return False
        if start_col < 0 or start_col + ship.get_size() > self.__num_cols:
            return False
        for col in range(start_col, start_col + ship.get_size()):
            if self.__board[row][col].has_ship():
                return False
        return True

    def __can_ship_fit_vertically(self, ship, start_row, col):
        if col < 0 or col >= self.__num_cols:
            return False
        if start_row < 0 or start_row + ship.get_size() > self.__num_rows:
            return False
        for row in range(start_row, start_row + ship.get_size()):
            if self.__board[row][col].has_ship():
                return False
        return True

    def get_board_attack_values(self):
        values = []
        for r in range(self.__num_rows):
            row = []
            for c in range(self.__num_cols):
                row.append(self.__board[r][c].get_cell_attack_value())
            values.append(row)
        return values

    def get_board_planning_values(self):
        values = []
        for r in range(self.__num_rows):
            row = []
            for c in range(self.__num_cols):
                row.append(self.__board[r][c].get_cell_planning_value())
            values.append(row)
        return values

    def ship_cells(self):
        cells = {}
        for r in range(self.__num_rows):
            for c in range(self.__num_cols):
                cell = self.__board[r][c]
                if cell.has_ship():
                    key = cell.get_ship().get_name()
                    cells.setdefault(key, []).append((r, c))
        return cells

    def get_remaining_ship_sizes(self):
        remaining = []
        seen = set()
        for r in range(self.__num_rows):
            for c in range(self.__num_cols):
                cell = self.__board[r][c]
                if cell.has_ship():
                    ship = cell.get_ship()
                    if ship.get_name() not in seen and not ship.is_sunk():
                        seen.add(ship.get_name())
                        remaining.append(ship.get_size())
        return remaining

    def to_state(self):
        return {
            "rows": self.__num_rows,
            "cols": self.__num_cols,
            "cells": [
                [
                    {
                        "hit": self.__board[r][c].is_hit(),
                        "ship": self.__board[r][c].get_ship().get_name() if self.__board[r][c].has_ship() else None,
                    }
                    for c in range(self.__num_cols)
                ]
                for r in range(self.__num_rows)
            ],
        }

    def save_board_state(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_state(), f, indent=2)

    def __format_console_value(self, cell, planning=False, easy_reveal=False):
        value = cell.get_cell_planning_value() if planning else cell.get_cell_attack_value()
        if easy_reveal and not planning and cell.has_ship() and not cell.is_hit():
            value = cell.get_ship().get_letter().lower()
        if cell.is_hit() and cell.has_ship():
            return self.RED + value + self.RESET
        if cell.is_hit() and not cell.has_ship():
            return self.WHITE + value + self.RESET
        return value

    def __show_board(self, planning=False, easy_reveal=False):
        header = "    " + " ".join(chr(65 + i) for i in range(self.__num_cols))
        print(header)
        for r in range(self.__num_rows):
            values = []
            for c in range(self.__num_cols):
                values.append(self.__format_console_value(self.__board[r][c], planning, easy_reveal))
            print(f"{r:>2}  " + " ".join(values))

    def show_board_attack(self, easy_reveal=False):
        self.__show_board(planning=False, easy_reveal=easy_reveal)

    def show_board_planning(self):
        self.__show_board(planning=True, easy_reveal=False)
