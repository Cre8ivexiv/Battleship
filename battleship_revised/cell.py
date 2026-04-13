# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 12:40:12 2024

@author: id126848
"""

class Cell:
    # The Cell class represents a cell of the grid (game board). Each cell has x and y
    # coordinates, a boolean attribute hit and a variable ship which will hold a reference
    # to the ship that is positioned on that cell (if any)
    
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
        return (self.__x, self.__y)
    
    def is_hit(self):
        return self.__hit
    
    def set_hit(self, hit):
        self.__hit = hit
    
    def get_ship(self):
        return self.__ship
    
    def set_ship(self, ship):
        self.__ship = ship
    
    def has_ship(self):
        return self.__ship != None
    
    def get_cell_attack_value(self):
        # If the cell is hit and has a ship, return the initial letter of the ship.
        # If the cell is hit but does not have a ship, return "O".
        # If the cell is not hit, return a space character.
        if not self.__hit:
            return " "
        if self.has_ship():
            return self.__ship.get_letter()
        return "O"
    
    def get_cell_planning_value(self):
        # If the cell is hit and has a ship, return the ship's initial letter.
        # If the cell is hit but does not have a ship, return "O".
        # If the cell is not hit and has a ship, return the ship's initial letter.
        # If the cell is not hit and has no ship, return a space character.
        if self.__hit and self.has_ship():
            return self.__ship.get_letter()
        if self.__hit and not self.has_ship():
            return "O"
        if self.has_ship():
            return self.__ship.get_letter()
        return " "
