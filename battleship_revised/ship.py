# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 12:27:35 2024

@author: id126848
"""

class Ship:
    # The Ship class represents a ship of the battleship game
    
    def __init__(self, name, size):
        self.__name = name
        self.__size = size
        self.__cells_list = []
    
    def get_name(self):
        return self.__name
    
    def get_size(self):
        return self.__size
    
    def get_letter(self):
        # Return the first character (initial) of the ship's name
        return self.__name[0].upper()
    
    def get_cells_list(self):
        return self.__cells_list
    
    def add_cell(self, cell):
        self.__cells_list.append(cell)
    
    def clear_cells(self):
        self.__cells_list = []
    
    def is_sunk(self):
        # Return True if the ship is sunk, else return False
        if len(self.__cells_list) == 0:
            return False
        for cell in self.__cells_list:
            if not cell.is_hit():
                return False
        return True
