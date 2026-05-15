import json
import os
from gameboard import GameBoard
from player import HumanPlayer, ComputerPlayer
from gamegui import GameGUI


def choose_difficulty():
    while True:
        difficulty = input("Choose difficulty (easy / medium / hard): ").strip().lower()
        if difficulty in ("easy", "medium", "hard"):
            return difficulty
        print("Please choose easy, medium, or hard.")


def save_console_game(filepath, p1, p2, current_player_index, difficulty):
    data = {
        "difficulty": difficulty,
        "current_player_index": current_player_index,
        "p1_plan": p1.get_plan_board().serialize(),
        "p1_attack": p1.get_attack_board().serialize(),
        "p2_plan": p2.get_plan_board().serialize(),
        "p2_attack": p2.get_attack_board().serialize(),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Game metadata saved to {filepath}")

def load_console_game(filepath):
    """Loads the board states and returns the reconstructed game variables."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    difficulty = data.get("difficulty", "medium")
    current_player_index = data.get("current_player_index", 0)
    
    gboard1, gboard2 = GameBoard(), GameBoard()
    p1 = HumanPlayer("Player 1", gboard1, gboard2, difficulty=difficulty)
    p2 = ComputerPlayer("Computer", gboard2, gboard1, difficulty=difficulty)

    # Reconstruct the boards using your existing logic
    gboard1.deserialize(data["p1_plan"], p1.get_ships_list())
    p1.get_attack_board().deserialize(data["p1_attack"]) # Attack boards don't need ship lists
    gboard2.deserialize(data["p2_plan"], p2.get_ships_list())
    p2.get_attack_board().deserialize(data["p2_attack"])
    
    print("\n✅ Game successfully loaded!")
    return p1, p2, current_player_index, difficulty
#
def console_main():
    save_file = "console_save.json"
    
    # Check if user wants to load a game
    if os.path.exists(save_file):
        load_choice = input("A saved game was found. Do you want to load it? (Y/N): ").strip().upper()
        if load_choice == "Y":
            try:
                p1, p2, current_player_index, difficulty = load_console_game(save_file)
                players_list = (p1, p2)
                print(f"Resuming game on {difficulty} difficulty...")
            except Exception as e:
                print(f"Failed to load game: {e}. Starting fresh.")
                load_choice = "N"
    else:
        load_choice = "N"

    # Start fresh if no load
    if load_choice != "Y":
        difficulty = choose_difficulty()
        gboard1 = GameBoard()
        gboard2 = GameBoard()
        p1 = HumanPlayer("Player 1", gboard1, gboard2, difficulty=difficulty)
        p2 = ComputerPlayer("Computer", gboard2, gboard1, difficulty=difficulty)

        while True:
            placement_choice = input("Place your fleet manually or randomly? (M/R): ").strip().upper()
            if placement_choice == "M":
                p1.position_ships_manually()
                break
            if placement_choice == "R":
                p1.position_ships_randomly()
                break
            print("Please enter M or R.")

        p2.position_ships_randomly()
        players_list = (p1, p2)
        current_player_index = 0

    # The Main Game Loop
    while True:
        current = players_list[current_player_index]
        if isinstance(current, HumanPlayer):
            current.show_boards()
            
        hit, result = current.play()

        # Handle Save request from the user
        if result.get("save_requested"):
            save_console_game(save_file, p1, p2, current_player_index, difficulty)
            print("Exiting game. See you next time!")
            break

        next_player_index = 0 if current_player_index == 1 else 1
        other = players_list[next_player_index]
        
        if other.has_lost_game():
            print(f"\n🎉 {current.get_player_name()} wins! 🎉")
            # Optionally delete save file here so they can't resume a finished game
            if os.path.exists(save_file):
                os.remove(save_file)
            break
            
        if not hit:
            current_player_index = next_player_index
        else:
            print(f"{current.get_player_name()} gets another turn because it was a hit!")


def main():
    print("Welcome to Battleship Game!")
    while True:
        print("Choose interface:")
        print("\t1. Console")
        print("\t2. GUI")
        choice = input("Enter number to choose interface or 'q' to quit: ").strip().lower()
        if choice == "q":
            break
        if choice == "1":
            console_main()
        elif choice == "2":
            GameGUI().initialise()
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
