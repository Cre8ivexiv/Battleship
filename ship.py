class Ship:
    """Represents a single ship in the Battleship game."""

    def __init__(self, name, symbol, size):
        self.__name = name
        self.__symbol = symbol
        self.__size = size
        self.__cells_list = []

    def get_name(self):
        return self.__name

    def get_symbol(self):
        return self.__symbol

    def get_letter(self):
        return self.__symbol

    def get_size(self):
        return self.__size

    def get_cells_list(self):
        return self.__cells_list

    def add_cell(self, cell):
        self.__cells_list.append(cell)

    def clear_cells(self):
        self.__cells_list = []

    def is_sunk(self):
        if not self.__cells_list:
            return False
        for cell in self.__cells_list:
            if not cell.is_hit():
                return False
        return True

    def engine_index(self):
        # A visual hint used only in easy mode.
        return len(self.__cells_list) // 2 if self.__cells_list else 0
