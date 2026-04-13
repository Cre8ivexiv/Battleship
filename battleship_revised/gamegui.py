import tkinter
from sys import exit
from tkinter import messagebox
from gameboard import GameBoard
from player import HumanPlayer
from player import ComputerPlayer

class GameGUI:
        
    def __init__(self):
        self.mw = tkinter.Tk()
        self.mw.title("Battleship Game")
        self.phase = "placement"
        self.current_ship_index = 0
        self.current_orientation = tkinter.StringVar(value="Horizontal")
        self.status_var = tkinter.StringVar(value="Place your ships on the planning board")
    
    def clicked_btn(self,x, y):
        if self.phase == "placement":
            self.__place_ship_gui(x, y)
            return
    
        p = self.players_list[self.current_player_index]
        attack_board = p.get_attack_board()
        if attack_board.is_space_free(x, y):
            attack_board.attack_cell(x, y)
            if isinstance(p, HumanPlayer):
                self.update_attack_button_text(x, y, p)
            else:
                self.update_plan_button_text(x, y, p)
            if attack_board.cell_has_hit_ship(x, y):
                message = "{} has hit the {}. ".format(p.get_player_name(), attack_board.get_cell_hit_ship_name(x, y))
                message += attack_board.get_cell_hit_ship_status(x, y)
                messagebox.showinfo("It's a hit!", message)
                extra_turn = True
            else:
                extra_turn = False
            next_player_index = 0 if self.current_player_index == 1 else 1
            next_player = self.players_list[next_player_index]
            if next_player.has_lost_game():
                self.winner = True
                messagebox.showinfo("Game Over", "{} wins!".format(p.get_player_name()))
                self.mw.destroy()
                exit()
            elif not extra_turn:
                self.current_player_index = next_player_index 
            p = self.players_list[self.current_player_index]
            if isinstance(p, ComputerPlayer):
                p.play()
                self.status_var.set("Your turn")
        
    def update_attack_button_text(self, x, y, player):
        button = self.attack_buttons_list[x][y]
        value = player.get_attack_board().get_board_attack_values()[x][y]
        button.config(text=value, state=tkinter.DISABLED)
        if player.get_attack_board().cell_has_hit_ship(x, y):
            button.config(bg="red", fg="white")
        elif value == "O":
            button.config(bg="light gray")
    
    def update_plan_button_text(self, x, y, player):
        button = self.plan_buttons_list[x][y]
        value = player.get_attack_board().get_board_attack_values()[x][y]
        button.config(text=value, state=tkinter.DISABLED)
        if player.get_attack_board().cell_has_hit_ship(x, y):
            button.config(bg="red", fg="white")
        elif value == "O":
            button.config(bg="light gray")
                
    def initialise(self):
        gboard1 = GameBoard()
        gboard2 = GameBoard()
        
        self.plan_buttons_list =  []
        for i in range (gboard1.get_num_rows()):
            row = [' '] * gboard1.get_num_cols()
            self.plan_buttons_list.append(row)
        
        self.attack_buttons_list =  []
        for i in range(gboard2.get_num_rows()):
            self.attack_buttons_list.append([' '] * gboard2.get_num_cols())
        
        self.cp_buttons_list =  []
        for i in range(gboard1.get_num_rows()):
            self.cp_buttons_list.append([' '] * gboard1.get_num_cols())
        
        p1 = HumanPlayer("Player 1", gboard1, gboard2)
        p2 = ComputerPlayer("Player 2", gboard2, gboard1, self.cp_buttons_list)
        p2.position_ships_randomly()
        self.__initialise_game(p1, p2)
        tkinter.mainloop()
    
    def __initialise_game(self, human_player, computer_player):
        self.players_list = (human_player, computer_player)
        self.current_player_index = 0
        self.winner = False
        
        top_panel = tkinter.Frame(self.mw, bd=4)
        top_panel.pack(side=tkinter.TOP, fill=tkinter.X)
        tkinter.Label(top_panel, textvariable=self.status_var).pack(side=tkinter.LEFT, padx=8)
        tkinter.Label(top_panel, text="Orientation:").pack(side=tkinter.LEFT)
        tkinter.OptionMenu(top_panel, self.current_orientation, "Horizontal", "Vertical").pack(side=tkinter.LEFT)
        tkinter.Button(top_panel, text="Restart", command=self.__restart).pack(side=tkinter.RIGHT, padx=8)
        
        planning_panel = tkinter.Frame(self.mw, relief=tkinter.RIDGE, bd=4)
        plan_board = human_player._get_plan_board()
        values = plan_board.get_board_planning_values()
        for i in range(plan_board.get_num_rows()):
            for j in range(plan_board.get_num_cols()):
                btn = tkinter.Button(planning_panel, text=values[i][j], width=3, command=lambda x=i, y=j: self.clicked_btn(x, y))
                btn.grid(row=i, column=j)
                self.plan_buttons_list[i][j] = btn
        planning_panel.pack(side=tkinter.LEFT)
        
        middle_panel = tkinter.Frame(self.mw, width=15, bd=4,relief=tkinter.RIDGE)
        middle_panel.pack(side=tkinter.LEFT)
        
        attack_panel = tkinter.Frame(self.mw, relief=tkinter.RIDGE, bd=4)
        attack_board = human_player.get_attack_board()
        for i in range(attack_board.get_num_rows()):
            for j in range(attack_board.get_num_cols()):
                btn = tkinter.Button(attack_panel, text=" ", width=3, state=tkinter.DISABLED, command=lambda x=i, y=j: self.clicked_btn(x, y))
                btn.grid(row=i, column=j)
                self.attack_buttons_list[i][j] = btn
                self.cp_buttons_list[i][j] = btn
        attack_panel.pack(side=tkinter.LEFT)
        
    def __place_ship_gui(self, x, y):
        human_player = self.players_list[0]
        ships = human_player.get_ships_list()
        if self.current_ship_index >= len(ships):
            return
        ship = ships[self.current_ship_index]
        orient = self.current_orientation.get()
        if human_player._get_plan_board().place_ship(ship, x, y, orient):
            values = human_player._get_plan_board().get_board_planning_values()
            for i in range(len(self.plan_buttons_list)):
                for j in range(len(self.plan_buttons_list[i])):
                    self.plan_buttons_list[i][j].config(text=values[i][j])
            self.current_ship_index += 1
            if self.current_ship_index == len(ships):
                self.phase = "battle"
                self.status_var.set("Battle started. Click the attack board to attack.")
                for i in range(len(self.attack_buttons_list)):
                    for j in range(len(self.attack_buttons_list[i])):
                        self.attack_buttons_list[i][j].config(state=tkinter.NORMAL)
            else:
                next_ship = ships[self.current_ship_index]
                self.status_var.set("Place {} (size {})".format(next_ship.get_name(), next_ship.get_size()))
        else:
            messagebox.showerror("Invalid placement", "Ship must stay in the board and cannot overlap.")

    def __restart(self):
        self.mw.destroy()
        main()


def main():
    b_gui = GameGUI()
    b_gui.initialise()    
        
if __name__ == "__main__":
    main()    
