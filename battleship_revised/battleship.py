# -*- coding: utf-8 -*-
"""
Created on 23rd Feb 2024

@author: Kostas Vlachos
"""

from gameboard import GameBoard
from player import HumanPlayer, ComputerPlayer
from gamegui import GameGUI


def main():
    
    # Create 2 game boards
    gboard1 = GameBoard()
    gboard2 = GameBoard()
    
    # Board 1 is the planning board for Player 1 and the attack board for Player 2.
    # Board 2 is the planning board for Player 2 and the attack board for Player 1.
    p1 = HumanPlayer("Player 1", gboard1, gboard2)
    p2 = ComputerPlayer("Player 2", gboard2, gboard1)
    
    # Human places ships manually; computer places randomly.
    p1.position_ships_manually()
    p2.position_ships_randomly()
    
    players_list = (p1, p2)
    current_player_index = 0
    winner = False
    
    while winner == False:
        p = players_list[current_player_index]
        if isinstance(p, HumanPlayer):
            p.show_boards()
        
        hit = p.play()
        
        next_player_index = 0 if current_player_index == 1 else 1
        next_player = players_list[next_player_index]
        if next_player.has_lost_game():
            winner = True
            print()
            print("%s is the Winner!" % p.get_player_name())
        elif not hit:
            current_player_index = next_player_index
        else:
            print("{} gets another turn because it was a hit!".format(p.get_player_name()))


if __name__ == "__main__":
    print("Welcome to Battleship Game!")
    while True:
        print("Choose interface:")
        print("\t 1. Console")
        print("\t 2. GUI")
        choice = input("Enter number to choose interface or 'q' to quit: ")
        if choice.lower() == "q":
            break
        if choice == "1":
            print("")
            main()
        elif choice == "2":
            b_gui = GameGUI()
            b_gui.initialise()
            break
