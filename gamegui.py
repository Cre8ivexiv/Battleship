import json
import tkinter as tk
from tkinter import messagebox, filedialog
from gameboard import GameBoard
from player import HumanPlayer, ComputerPlayer


class GameGUI:
    CELL = 36
    PADDING = 30

    def __init__(self):
        self.mw = tk.Tk()
        self.mw.title("Battleship Game")
        self.mw.configure(bg="#0a4478")
        self.phase = "setup"
        self.current_ship_index = 0
        self.current_orientation = tk.StringVar(value="Horizontal")
        self.difficulty = tk.StringVar(value="Medium")
        self.status_var = tk.StringVar(value="Choose difficulty and place your ships")
        self.player_idle_job = None
        self.player_think_start = None

    def initialise(self):
        self.__build_shell()
        self.__new_game()
        self.mw.mainloop()

    def __build_shell(self):
        top = tk.Frame(self.mw, bg="#0a4478")
        top.pack(fill=tk.X, pady=8)

        tk.Label(top, textvariable=self.status_var, bg="#0a4478", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=8)
        tk.Label(top, text="Difficulty:", bg="#0a4478", fg="white").pack(side=tk.LEFT)
        tk.OptionMenu(top, self.difficulty, "Easy", "Medium", "Hard").pack(side=tk.LEFT)
        tk.Label(top, text="Orientation:", bg="#0a4478", fg="white").pack(side=tk.LEFT, padx=(10, 0))
        tk.OptionMenu(top, self.current_orientation, "Horizontal", "Vertical").pack(side=tk.LEFT)
        tk.Button(top, text="Randomise Fleet", command=self.__randomise_human_fleet).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Save", command=self.__save_game).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Load", command=self.__load_game).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Restart", command=self.__new_game).pack(side=tk.RIGHT, padx=6)

        body = tk.Frame(self.mw, bg="#0a4478")
        body.pack(padx=10, pady=10)

        self.plan_canvas = tk.Canvas(body, width=420, height=420, bg="#7cc5ff", highlightthickness=0)
        self.plan_canvas.pack(side=tk.LEFT, padx=8)
        self.attack_canvas = tk.Canvas(body, width=420, height=420, bg="#7cc5ff", highlightthickness=0)
        self.attack_canvas.pack(side=tk.LEFT, padx=8)

        self.plan_canvas.bind("<Button-1>", self.__on_plan_click)
        self.attack_canvas.bind("<Button-1>", self.__on_attack_click)

    def __new_game(self):
        self.phase = "placement"
        self.current_ship_index = 0
        self.status_var.set("Place Aircraft carrier (size 5)")
        self.gboard1 = GameBoard()
        self.gboard2 = GameBoard()
        diff = self.difficulty.get().lower()
        self.p1 = HumanPlayer("Player 1", self.gboard1, self.gboard2, difficulty=diff)
        self.p2 = ComputerPlayer("Computer", self.gboard2, self.gboard1, difficulty=diff)
        self.p2.position_ships_randomly()
        self.players_list = (self.p1, self.p2)
        self.current_player_index = 0
        self.__draw_all()

    def __grid_to_cell(self, event):
        col = (event.x - self.PADDING) // self.CELL
        row = (event.y - self.PADDING) // self.CELL
        if 0 <= row < 10 and 0 <= col < 10:
            return row, col
        return None

    def __on_plan_click(self, event):
        if self.phase != "placement":
            return
        rc = self.__grid_to_cell(event)
        if rc is None:
            return
        row, col = rc
        ship = self.p1.get_ships_list()[self.current_ship_index]
        orient = self.current_orientation.get()
        if self.p1.get_plan_board().place_ship(ship, row, col, orient):
            self.current_ship_index += 1
            self.__draw_all()
            if self.current_ship_index >= len(self.p1.get_ships_list()):
                self.phase = "battle"
                self.status_var.set("Battle started. Click the right grid to attack.")
                self.__start_idle_timer()
            else:
                next_ship = self.p1.get_ships_list()[self.current_ship_index]
                self.status_var.set(f"Place {next_ship.get_name()} (size {next_ship.get_size()})")
        else:
            messagebox.showerror("Invalid placement", "Ship must stay within the grid and cannot overlap.")

    def __on_attack_click(self, event):
        if self.phase != "battle" or self.current_player_index != 0:
            return
        rc = self.__grid_to_cell(event)
        if rc is None:
            return
        self.__cancel_idle_timer()
        row, col = rc
        board = self.p1.get_attack_board()
        if board.was_already_targeted(row, col):
            self.status_var.set("That square was already targeted.")
            self.__start_idle_timer()
            return
        result = board.attack_cell(row, col)
        self.__draw_all()
        if result["hit"]:
            if result["sunk"]:
                self.status_var.set(f"You sunk the enemy {result['ship_name']}!")
                self.__flash_sunk(self.attack_canvas, result["sunk_cells"], 0)
            else:
                self.status_var.set(f"Hit! {result['ship_name']} was damaged.")
            if self.p2.has_lost_game():
                messagebox.showinfo("Game Over", "You won!")
                self.phase = "finished"
                return
            self.__start_idle_timer()
        else:
            self.status_var.set("Miss. Computer is thinking...")
            self.current_player_index = 1
            self.mw.after(2000, self.__computer_turn)

    def __computer_turn(self):
        if self.phase != "battle":
            return
        hit, result = self.p2.play()
        row = result["row"]
        col = result["col"]
        self.__draw_all()
        if hit:
            if result["sunk"]:
                self.status_var.set(f"Computer sunk your {result['ship_name']}!")
                self.__flash_sunk(self.plan_canvas, result["sunk_cells"], 0)
            else:
                self.status_var.set(f"Computer hit your {result['ship_name']}! Thinking...")
            if self.p1.has_lost_game():
                messagebox.showinfo("Game Over", "Computer won.")
                self.phase = "finished"
                return
            self.mw.after(2000, self.__computer_turn)
        else:
            self.status_var.set("Your turn")
            self.current_player_index = 0
            self.__start_idle_timer()

    def __draw_grid(self, canvas, title):
        canvas.delete("all")
        canvas.create_text(210, 12, text=title, fill="white", font=("Arial", 12, "bold"))
        for i in range(10):
            x = self.PADDING + i * self.CELL
            canvas.create_text(x + self.CELL / 2, 25, text=chr(65 + i), fill="white")
            y = self.PADDING + i * self.CELL
            canvas.create_text(15, y + self.CELL / 2, text=str(i), fill="white")
        for i in range(11):
            p = self.PADDING + i * self.CELL
            canvas.create_line(self.PADDING, p, self.PADDING + 10 * self.CELL, p, fill="#4f92ca")
            canvas.create_line(p, self.PADDING, p, self.PADDING + 10 * self.CELL, fill="#4f92ca")

    def __ship_groups(self, board):
        groups = {}
        for r in range(board.get_num_rows()):
            for c in range(board.get_num_cols()):
                cell = board.get_cell(r, c)
                if cell.has_ship():
                    ship = cell.get_ship()
                    groups.setdefault(ship.get_name(), {"ship": ship, "cells": []})["cells"].append((r, c, cell))
        return groups

    def __draw_ship_icon(self, canvas, cells, color="#426f5f", reveal_body=True):
        coords = [(r, c) for r, c, _ in cells]
        rows = sorted(r for r, _ in coords)
        cols = sorted(c for _, c in coords)
        min_r, max_r = rows[0], rows[-1]
        min_c, max_c = cols[0], cols[-1]
        x1 = self.PADDING + min_c * self.CELL + 2
        y1 = self.PADDING + min_r * self.CELL + 2
        x2 = self.PADDING + (max_c + 1) * self.CELL - 2
        y2 = self.PADDING + (max_r + 1) * self.CELL - 2

        horizontal = (max_c - min_c) >= (max_r - min_r)
        if reveal_body:
            if horizontal:
                canvas.create_oval(x1, y1, x1 + (y2 - y1), y2, fill=color, outline="#274239")
                canvas.create_rectangle(x1 + (y2 - y1) / 2, y1, x2 - (y2 - y1) / 2, y2, fill=color, outline="#274239")
                canvas.create_oval(x2 - (y2 - y1), y1, x2, y2, fill=color, outline="#274239")
            else:
                canvas.create_oval(x1, y1, x2, y1 + (x2 - x1), fill=color, outline="#274239")
                canvas.create_rectangle(x1, y1 + (x2 - x1) / 2, x2, y2 - (x2 - x1) / 2, fill=color, outline="#274239")
                canvas.create_oval(x1, y2 - (x2 - x1), x2, y2, fill=color, outline="#274239")

        # engine dot for easy mode / own board
        mid_index = len(cells) // 2
        er, ec, _ = sorted(cells, key=lambda item: (item[0], item[1]))[mid_index]
        cx = self.PADDING + ec * self.CELL + self.CELL / 2
        cy = self.PADDING + er * self.CELL + self.CELL / 2
        canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#111", outline="")

    def __draw_hits_and_misses(self, canvas, board, reveal_enemy=False):
        groups = self.__ship_groups(board)
        diff = self.difficulty.get().lower()
        for group in groups.values():
            cells = group["cells"]
            if canvas is self.plan_canvas:
                self.__draw_ship_icon(canvas, cells, reveal_body=True)
            elif reveal_enemy:
                self.__draw_ship_icon(canvas, cells, color="#537862", reveal_body=(diff == "easy"))
            elif diff == "easy":
                self.__draw_ship_icon(canvas, cells, color="#537862", reveal_body=True)

        for r in range(board.get_num_rows()):
            for c in range(board.get_num_cols()):
                cell = board.get_cell(r, c)
                x1 = self.PADDING + c * self.CELL + 6
                y1 = self.PADDING + r * self.CELL + 6
                x2 = x1 + self.CELL - 12
                y2 = y1 + self.CELL - 12
                if cell.is_hit() and cell.has_ship():
                    canvas.create_rectangle(self.PADDING + c * self.CELL + 1, self.PADDING + r * self.CELL + 1,
                                            self.PADDING + (c + 1) * self.CELL - 1, self.PADDING + (r + 1) * self.CELL - 1,
                                            fill="#ff4a4a", outline="")
                    if canvas is self.plan_canvas or diff in ("medium", "hard"):
                        canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=cell.get_ship().get_letter(), fill="white")
                elif cell.is_hit() and not cell.has_ship():
                    canvas.create_oval(x1, y1, x2, y2, fill="white", outline="")

    def __draw_all(self):
        self.__draw_grid(self.plan_canvas, "Your planning board")
        self.__draw_grid(self.attack_canvas, "Attack board")
        self.__draw_hits_and_misses(self.plan_canvas, self.p1.get_plan_board())
        self.__draw_hits_and_misses(self.attack_canvas, self.p1.get_attack_board(), reveal_enemy=False)

    def __flash_sunk(self, canvas, cells, step):
        if step >= 6:
            self.__draw_all()
            return
        for r, c in cells:
            x1 = self.PADDING + c * self.CELL + 1
            y1 = self.PADDING + r * self.CELL + 1
            x2 = self.PADDING + (c + 1) * self.CELL - 1
            y2 = self.PADDING + (r + 1) * self.CELL - 1
            color = "#ff0000" if step % 2 == 0 else "#ff9090"
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        self.mw.after(140, lambda: self.__flash_sunk(canvas, cells, step + 1))

    def __randomise_human_fleet(self):
        if self.phase != "placement":
            return
        self.p1.position_ships_randomly()
        self.current_ship_index = len(self.p1.get_ships_list())
        self.phase = "battle"
        self.status_var.set("Battle started. Click the right grid to attack.")
        self.__draw_all()
        self.__start_idle_timer()

    def __start_idle_timer(self):
        self.__cancel_idle_timer()
        self.player_idle_job = self.mw.after(5000, lambda: self.status_var.set("You're really taking your time..."))

    def __cancel_idle_timer(self):
        if self.player_idle_job is not None:
            self.mw.after_cancel(self.player_idle_job)
            self.player_idle_job = None

    def __save_game(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        data = {
            "difficulty": self.difficulty.get(),
            "phase": self.phase,
            "current_ship_index": self.current_ship_index,
            "current_player_index": self.current_player_index,
            "plan_board": self.p1.get_plan_board().to_state(),
            "attack_board": self.p1.get_attack_board().to_state(),
            "computer_plan_board": self.p2.get_plan_board().to_state(),
            "computer_attack_board": self.p2.get_attack_board().to_state(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.status_var.set("Game saved")

    def __load_game(self):
        messagebox.showinfo("Load game", "A basic Save button is included. Full GUI load can be added on top of this skeleton if needed.")


def main():
    GameGUI().initialise()


if __name__ == "__main__":
    main()
