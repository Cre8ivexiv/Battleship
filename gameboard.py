import json
from cell import Cell
from ship import Ship


class GameBoard:
    RED = "\033[31m"
    WHITE = "\033[97m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    def __init__(self, num_rows=10, num_cols=10):
        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__chain_triggered_ships = set()
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
        self.__chain_triggered_ships.clear()

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
        was_sunk_before = cell.has_ship() and cell.get_ship().is_sunk()
        cell.set_hit(True)
        result = {
            "hit": cell.has_ship(),
            "miss": not cell.has_ship(),
            "ship_name": None,
            "ship_symbol": None,
            "sunk": False,
            "sunk_cells": [],
            "chain_hits": [],
            "chain_sunk": [],
        }
        if cell.has_ship():
            ship = cell.get_ship()
            result["ship_name"] = ship.get_name()
            result["ship_symbol"] = ship.get_letter()
            result["sunk"] = ship.is_sunk()
            if result["sunk"]:
                result["sunk_cells"] = [c.get_coords() for c in ship.get_cells_list()]
                if not was_sunk_before:
                    self.__apply_chain_damage(ship, result)
        return result

    def __apply_chain_damage(self, ship, result):
        ship_key = id(ship)
        if ship_key in self.__chain_triggered_ships:
            return
        self.__chain_triggered_ships.add(ship_key)

        for row, col in self.__ship_radius_cells(ship):
            cell = self.__board[row][col]
            if cell in ship.get_cells_list():
                continue
            was_hit = cell.is_hit()
            was_sunk_before = cell.has_ship() and cell.get_ship().is_sunk()
            cell.set_hit(True)
            if not was_hit:
                result["chain_hits"].append((row, col))
            if cell.has_ship():
                affected_ship = cell.get_ship()
                if affected_ship.is_sunk() and not was_sunk_before:
                    sunk_cells = [c.get_coords() for c in affected_ship.get_cells_list()]
                    result["chain_sunk"].append({
                        "ship_name": affected_ship.get_name(),
                        "ship_symbol": affected_ship.get_letter(),
                        "sunk_cells": sunk_cells,
                    })
                    self.__apply_chain_damage(affected_ship, result)

    def __ship_radius_cells(self, ship):
        radius_cells = set()
        for cell in ship.get_cells_list():
            row, col = cell.get_coords()
            for rr in range(row - 1, row + 2):
                for cc in range(col - 1, col + 2):
                    if 0 <= rr < self.__num_rows and 0 <= cc < self.__num_cols:
                        radius_cells.add((rr, cc))
        return radius_cells

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

    def remove_ship(self, ship):
        for row in range(self.__num_rows):
            for col in range(self.__num_cols):
                cell = self.__board[row][col]
                if cell.get_ship() is ship:
                    cell.set_ship(None)
                    cell.set_hit(False)
        ship.clear_cells()

    def get_ship_position_cells(self, ship, row, col, orient="Horizontal"):
        if orient == "Horizontal":
            start_col = self.__fit_horizontal_start(ship, col)
            if row < 0 or row >= self.__num_rows:
                return []
            return [(row, c) for c in range(start_col, start_col + ship.get_size())]
        if orient == "Vertical":
            start_row = self.__fit_vertical_start(ship, row)
            if col < 0 or col >= self.__num_cols:
                return []
            return [(r, col) for r in range(start_row, start_row + ship.get_size())]
        return []

    def can_place_ship_at(self, ship, row, col, orient="Horizontal", ignore_ship=None, require_spacing=False):
        cells = self.get_ship_position_cells(ship, row, col, orient)
        if len(cells) != ship.get_size():
            return False
        for r, c in cells:
            existing_ship = self.__board[r][c].get_ship()
            if existing_ship is not None and existing_ship is not ignore_ship:
                return False
        if require_spacing:
            for r, c in cells:
                for rr in range(r - 1, r + 2):
                    for cc in range(c - 1, c + 2):
                        if 0 <= rr < self.__num_rows and 0 <= cc < self.__num_cols:
                            nearby_ship = self.__board[rr][cc].get_ship()
                            if nearby_ship is not None and nearby_ship is not ignore_ship:
                                return False
        return True

    def place_ship_with_spacing(self, ship, row, col, orient="Horizontal"):
        if not self.can_place_ship_at(ship, row, col, orient, require_spacing=True):
            return False
        return self.place_ship(ship, row, col, orient)

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

    def serialize(self):
        return {
            "rows": self.__num_rows,
            "cols": self.__num_cols,
            "cells": [
                [
                    {
                        "hit": self.__board[r][c].is_hit(),
                        "ship": self.__serialize_ship(self.__board[r][c].get_ship()) if self.__board[r][c].has_ship() else None,
                    }
                    for c in range(self.__num_cols)
                ]
                for r in range(self.__num_rows)
            ],
        }

    def __serialize_ship(self, ship):
        return {
            "name": ship.get_name(),
            "symbol": ship.get_letter(),
            "size": ship.get_size(),
        }

    def deserialize(self, data, ships_list=None):
        rows = data.get("rows", self.__num_rows)
        cols = data.get("cols", self.__num_cols)
        if rows != self.__num_rows or cols != self.__num_cols:
            self.__num_rows = rows
            self.__num_cols = cols
            self.__board = []
            for r in range(self.__num_rows):
                row = []
                for c in range(self.__num_cols):
                    row.append(Cell(r, c))
                self.__board.append(row)

        if ships_list is None:
            ships_list = []
        for ship in ships_list:
            ship.clear_cells()

        ship_lookup = {}
        for ship in ships_list:
            ship_lookup[ship.get_name()] = ship
            ship_lookup[ship.get_letter()] = ship

        for r in range(self.__num_rows):
            for c in range(self.__num_cols):
                self.__board[r][c].set_ship(None)
                self.__board[r][c].set_hit(False)

        for r, row_data in enumerate(data.get("cells", [])):
            if r >= self.__num_rows:
                break
            for c, cell_data in enumerate(row_data):
                if c >= self.__num_cols:
                    break
                cell = self.__board[r][c]
                ship_info = cell_data.get("ship")
                if ship_info:
                    ship = self.__get_deserialized_ship(ship_info, ship_lookup)
                    cell.set_ship(ship)
                    ship.add_cell(cell)
                cell.set_hit(bool(cell_data.get("hit", False)))
        self.__chain_triggered_ships.clear()

    def __get_deserialized_ship(self, ship_info, ship_lookup):
        if isinstance(ship_info, dict):
            name = ship_info.get("name")
            symbol = ship_info.get("symbol")
            size = ship_info.get("size", 0)
        else:
            name = ship_info
            symbol = None
            size = 0

        ship = ship_lookup.get(name)
        if ship is None and symbol is not None:
            ship = ship_lookup.get(symbol)
        if ship is None:
            symbol = symbol or (name[:1].upper() if name else "?")
            ship = Ship(name, symbol, size)
            ship_lookup[name] = ship
            ship_lookup[symbol] = ship
        return ship

    def to_state(self):
        return self.serialize()

    def save_board_state(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.serialize(), f, indent=2)

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
