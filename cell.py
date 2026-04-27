class Cell:
    """Represents a single cell of a game board."""

    def __init__(self, x, y, hit=False):
        self.__x = x
        self.__y = y
        self.__hit = hit
        self.__ship = None

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def get_coords(self):
        return self.__x, self.__y

    def is_hit(self):
        return self.__hit

    def set_hit(self, hit):
        self.__hit = hit

    def get_ship(self):
        return self.__ship

    def set_ship(self, ship):
        self.__ship = ship

    def has_ship(self):
        return self.__ship is not None

    def get_cell_attack_value(self):
        if not self.__hit:
            return " "
        if self.has_ship():
            return self.__ship.get_letter()
        return "O"

    def get_cell_planning_value(self):
        if self.__hit and self.has_ship():
            return self.__ship.get_letter()
        if self.__hit and not self.has_ship():
            return "O"
        if self.has_ship():
            return self.__ship.get_letter()
        return " "
