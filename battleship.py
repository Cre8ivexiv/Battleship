import json
from gameboard import GameBoard
from player import HumanPlayer, ComputerPlayer
from gamegui import GameGUI


def choose_difficulty():
    while True:
        difficulty = input("Choose difficulty (easy / medium / hard): ").strip().lower()
        if difficulty in ("easy", "medium", "hard"):
            return difficulty
        print("Please choose easy, medium, or hard.")


def save_console_game(filepath, players_list, current_player_index, difficulty):
    data = {
        "difficulty": difficulty,
        "current_player_index": current_player_index,
        "players": [p.to_state() for p in players_list],
        "note": "Console save stores metadata. Full board reconstruction can be extended if your tutor requires it.",
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Game metadata saved to {filepath}")


def console_main():
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
    while True:
        current = players_list[current_player_index]
        if isinstance(current, HumanPlayer):
            current.show_boards()
            print("Type SAVE at any attack prompt to save metadata and continue later.")
        hit, result = current.play()

        next_player_index = 0 if current_player_index == 1 else 1
        other = players_list[next_player_index]
        if other.has_lost_game():
            print(f"\n{current.get_player_name()} wins!")
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
