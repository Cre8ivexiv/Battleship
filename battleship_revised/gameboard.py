from cell import Cell

class GameBoard:
    
    def __init__(self, num_rows=10, num_cols=10):
        self.__space = ' '
        self.__num_rows = num_rows
        self.__num_cols = num_cols
        self.__board =  []
            
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
    
    def is_space_free(self, row, col):
        # Return True if the space (cell) in place row, col has not been hit.
        if row < 0 or row >= self.__num_rows or col < 0 or col >= self.__num_cols:
            return False
        return not self.__board[row][col].is_hit()
    
    def attack_cell(self, row, col):
        self.__board[row][col].set_hit(True)
    
    def cell_has_hit_ship(self, row, col):
        # Return True if the cell in place row, col has been hit and has ship.
        return self.__board[row][col].is_hit() and self.__board[row][col].has_ship()
    
    def get_cell_hit_ship_name(self, row, col):
        if self.cell_has_hit_ship(row, col):
            return self.__board[row][col].get_ship().get_name()
        return None
    
    def get_cell_hit_ship_status(self, row, col):
        if self.cell_has_hit_ship(row, col):
            ship = self.__board[row][col].get_ship()
            if ship.is_sunk():
                return "{} has been sunk!".format(ship.get_name())
            num_hits = 0
            for cell in ship.get_cells_list():
                if cell.is_hit():
                    num_hits += 1
            return "{} has been hit {} time(s).".format(ship.get_name(), num_hits)
        return None
    
    def place_ship(self, ship, row, col, orient="Horizontal"):
        if orient == "Horizontal":
            return self.__place_ship_horizontally(ship, row, col)
        elif orient == "Vertical":
            return self.__place_ship_vertically(ship, row, col)
        else:
            print("Incorrect orientation; should be 'Horizontal' or 'Vertical'")
            return False
    
    def __place_ship_horizontally(self, ship, row, start_col):
        if self.__can_ship_fit_horizontally(ship, row, start_col):
            ship.clear_cells()
            for col in range(start_col, start_col + ship.get_size()):
                self.__board[row][col].set_ship(ship)
                ship.add_cell(self.__board[row][col])
            return True
        return False
    
    def __place_ship_vertically(self, ship, start_row, col):
        if self.__can_ship_fit_vertically(ship, start_row, col):
            ship.clear_cells()
            for row in range(start_row, start_row + ship.get_size()):
                self.__board[row][col].set_ship(ship)
                ship.add_cell(self.__board[row][col])
            return True
        return False
    
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
    
    def show_board_attack(self):
        self.__show_board(self.get_board_attack_values(), attack_mode=True)
    
    def show_board_planning(self):
        self.__show_board(self.get_board_planning_values(), attack_mode=False)

    def __show_board(self, values, attack_mode=False):
        red = "\033[91m"
        reset = "\033[0m"
        header = "   " + " ".join(chr(65 + i) for i in range(self.__num_cols))
        print(header)
        for r in range(self.__num_rows):
            row_str = f"{r:2} "
            for c in range(self.__num_cols):
                val = values[r][c]
                cell = self.__board[r][c]
                if cell.is_hit() and cell.has_ship():
                    row_str += red + val + reset
                else:
                    row_str += val
                if c != self.__num_cols - 1:
                    row_str += " "
            print(row_str)
