import json
import os
import random
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from gameboard import GameBoard
from player import HumanPlayer, ComputerPlayer


class GameGUI:
    CELL = 36
    PADDING = 30
    BOARD_SIZE = 420
    BOARD_GAP = 40
    PLAN_BOARD = "plan"
    ATTACK_BOARD = "attack"
    SHIP_IMAGE_FILES = {
        "A": "aircraft_carrier.png",
        "B": "battleship.png",
        "C": "cruiser.png",
        "S": "submarine.png",
        "D": "destroyer.png",
    }

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
        self.ship_image_cache = {}
        self.ship_image_refs = []
        self.background_image = None
        self.background_photo = None
        self.drag_data = None
        self.warning_cells = set()
        self.selected_ship = None
        self.ship_orientations = {}

    def initialise(self):
        self.__build_shell()
        self.__new_game()
        self.mw.mainloop()

    def __build_shell(self):
        self.mw.geometry("1000x560")
        self.__load_background()

        top = tk.Frame(self.mw, bg="#0a4478")
        top.pack(fill=tk.X, pady=8)

        tk.Label(top, textvariable=self.status_var, bg="#0a4478", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=8)
        tk.Label(top, text="Difficulty:", bg="#0a4478", fg="white").pack(side=tk.LEFT)
        tk.OptionMenu(top, self.difficulty, "Easy", "Medium", "Hard").pack(side=tk.LEFT)
        tk.Label(top, text="Orientation:", bg="#0a4478", fg="white").pack(side=tk.LEFT, padx=(10, 0))
        tk.OptionMenu(top, self.current_orientation, "Horizontal", "Vertical", command=self.__on_orientation_change).pack(side=tk.LEFT)
        self.start_button = tk.Button(top, text="Start", command=self.__start_game)
        self.start_button.pack(side=tk.RIGHT, padx=6)
        self.randomise_button = tk.Button(top, text="Randomise Fleet", command=self.__randomise_human_fleet)
        self.randomise_button.pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Save", command=self.__save_game).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Load", command=self.__load_game).pack(side=tk.RIGHT, padx=6)
        tk.Button(top, text="Restart", command=self.__new_game).pack(side=tk.RIGHT, padx=6)

        body = tk.Frame(self.mw, bg="#0a4478")
        body.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        canvas_width = self.BOARD_SIZE * 2 + self.BOARD_GAP
        self.game_canvas = tk.Canvas(body, width=canvas_width, height=self.BOARD_SIZE, highlightthickness=0)
        self.game_canvas.pack(fill=tk.BOTH, expand=True)
        self.plan_canvas = self.game_canvas
        self.attack_canvas = self.game_canvas

        self.game_canvas.bind("<Configure>", self.__on_canvas_resize)
        self.game_canvas.bind("<ButtonPress-1>", self.__on_canvas_press)
        self.game_canvas.bind("<B1-Motion>", self.__on_plan_drag)
        self.game_canvas.bind("<ButtonRelease-1>", self.__on_plan_release)
        self.game_canvas.bind("<Button-3>", self.__on_plan_rotate)

    def __load_background(self):
        image_path = os.path.join(os.path.dirname(__file__), "battleship_background.png")
        if not os.path.exists(image_path):
            return
        self.background_image = Image.open(image_path).convert("RGB")

    def __on_canvas_resize(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        if hasattr(self, "p1"):
            self.__draw_all()

    def __draw_background(self):
        width = max(self.game_canvas.winfo_width(), self.BOARD_SIZE * 2 + self.BOARD_GAP)
        height = max(self.game_canvas.winfo_height(), self.BOARD_SIZE)
        if self.background_image is None:
            self.game_canvas.create_rectangle(0, 0, width, height, fill="#082f4a", outline="")
            return
        resized = self.background_image.resize((width, height), Image.Resampling.LANCZOS)
        self.background_photo = ImageTk.PhotoImage(resized)
        self.game_canvas.create_image(0, 0, image=self.background_photo, anchor=tk.NW)

    def __new_game(self):
        self.__cancel_idle_timer()
        self.phase = "placement"
        self.current_ship_index = 0
        self.drag_data = None
        self.warning_cells = set()
        self.selected_ship = None
        self.ship_orientations = {}
        self.status_var.set("Drag ships on your board, right-click to rotate, then press Start")
        self.gboard1 = GameBoard()
        self.gboard2 = GameBoard()
        diff = self.difficulty.get().lower()
        self.p1 = HumanPlayer("Player 1", self.gboard1, self.gboard2, difficulty=diff)
        self.p2 = ComputerPlayer("Computer", self.gboard2, self.gboard1, difficulty=diff)
        self.__randomise_player_fleet(self.p1)
        self.__randomise_player_fleet(self.p2)
        self.players_list = (self.p1, self.p2)
        self.current_player_index = 0
        self.start_button.config(state=tk.NORMAL)
        self.randomise_button.config(state=tk.NORMAL)
        self.__draw_all()

    def __board_origin(self, board_name):
        if board_name == self.ATTACK_BOARD:
            return self.BOARD_SIZE + self.BOARD_GAP, 0
        return 0, 0

    def __cell_bounds(self, board_name, row, col, inset=0):
        origin_x, origin_y = self.__board_origin(board_name)
        x1 = origin_x + self.PADDING + col * self.CELL + inset
        y1 = origin_y + self.PADDING + row * self.CELL + inset
        x2 = origin_x + self.PADDING + (col + 1) * self.CELL - inset
        y2 = origin_y + self.PADDING + (row + 1) * self.CELL - inset
        return x1, y1, x2, y2

    def __grid_to_cell(self, event, board_name):
        origin_x, origin_y = self.__board_origin(board_name)
        local_x = event.x - origin_x
        local_y = event.y - origin_y
        col = (local_x - self.PADDING) // self.CELL
        row = (local_y - self.PADDING) // self.CELL
        if 0 <= row < 10 and 0 <= col < 10:
            return row, col
        return None

    def __on_canvas_press(self, event):
        if self.phase == "placement":
            self.__on_plan_press(event)
        elif self.phase == "battle":
            self.__on_attack_click(event)

    def __ship_at_cell(self, board, row, col):
        cell = board.get_cell(row, col)
        if cell.has_ship():
            return cell.get_ship()
        return None

    def __ship_orientation(self, ship):
        if ship in self.ship_orientations:
            return self.ship_orientations[ship]
        cells = ship.get_cells_list()
        if len(cells) < 2:
            return self.current_orientation.get()
        rows = {cell.get_x() for cell in cells}
        return "Horizontal" if len(rows) == 1 else "Vertical"

    def __ship_cells_for_position(self, ship, row, col, orientation):
        cells = []
        for offset in range(ship.get_size()):
            if orientation == "Horizontal":
                cells.append((row, col + offset))
            else:
                cells.append((row + offset, col))
        return cells

    def __can_place_ship(self, board, ship, row, col, orientation, ignore_ship=None):
        cells = self.__ship_cells_for_position(ship, row, col, orientation)
        for r, c in cells:
            if r < 0 or r >= board.get_num_rows() or c < 0 or c >= board.get_num_cols():
                return False
            existing_ship = board.get_cell(r, c).get_ship()
            if existing_ship is not None and existing_ship is not ignore_ship:
                return False
        return True

    def __place_ship_strict(self, board, ship, row, col, orientation, ignore_ship=None):
        if not self.__can_place_ship(board, ship, row, col, orientation, ignore_ship=ignore_ship):
            return False
        board.remove_ship(ship)
        ship.clear_cells()
        for r, c in self.__ship_cells_for_position(ship, row, col, orientation):
            cell = board.get_cell(r, c)
            cell.set_ship(ship)
            cell.set_hit(False)
            ship.add_cell(cell)
        self.ship_orientations[ship] = orientation
        return True

    def __ship_anchor(self, ship):
        cells = ship.get_cells_list()
        if not cells:
            return 0, 0
        return min((cell.get_x(), cell.get_y()) for cell in cells)

    def __on_plan_press(self, event):
        if self.phase != "placement":
            return
        rc = self.__grid_to_cell(event, self.PLAN_BOARD)
        if rc is None:
            return
        row, col = rc
        board = self.p1.get_plan_board()
        ship = self.__ship_at_cell(board, row, col)
        if ship is None:
            return
        self.selected_ship = ship
        self.current_orientation.set(self.__ship_orientation(ship))
        anchor_row, anchor_col = self.__ship_anchor(ship)
        self.drag_data = {
            "ship": ship,
            "orientation": self.__ship_orientation(ship),
            "original_cells": [(cell.get_x(), cell.get_y()) for cell in ship.get_cells_list()],
            "original_orientation": self.__ship_orientation(ship),
            "offset_row": row - anchor_row,
            "offset_col": col - anchor_col,
            "preview_row": anchor_row,
            "preview_col": anchor_col,
        }
        board.remove_ship(ship)
        self.__update_drag_preview(event)

    def __on_plan_drag(self, event):
        if self.phase != "placement" or self.drag_data is None:
            return
        self.__update_drag_preview(event)

    def __on_plan_release(self, event):
        if self.phase != "placement" or self.drag_data is None:
            return
        board = self.p1.get_plan_board()
        ship = self.drag_data["ship"]
        row = self.drag_data["preview_row"]
        col = self.drag_data["preview_col"]
        orient = self.drag_data["orientation"]
        if self.__place_ship_strict(board, ship, row, col, orient):
            self.status_var.set("Ship moved. Press Start when ready.")
        else:
            self.__restore_dragged_ship()
            messagebox.showerror("Invalid placement", "Ship must stay inside the grid and cannot overlap another ship.")
            self.status_var.set("Invalid placement: ships cannot overlap or leave the grid.")
        self.drag_data = None
        self.warning_cells = set()
        self.__draw_all()

    def __on_plan_rotate(self, event):
        if self.phase != "placement":
            return
        rc = self.__grid_to_cell(event, self.PLAN_BOARD)
        if rc is None:
            return
        board = self.p1.get_plan_board()
        row, col = rc
        ship = self.__ship_at_cell(board, row, col)
        if ship is None:
            return
        self.selected_ship = ship
        anchor_row, anchor_col = self.__ship_anchor(ship)
        new_orient = "Vertical" if self.__ship_orientation(ship) == "Horizontal" else "Horizontal"
        original = [(cell.get_x(), cell.get_y()) for cell in ship.get_cells_list()]
        if self.__can_place_ship(board, ship, anchor_row, anchor_col, new_orient, ignore_ship=ship):
            self.__place_ship_strict(board, ship, anchor_row, anchor_col, new_orient, ignore_ship=ship)
            self.current_orientation.set(new_orient)
            self.status_var.set(f"{ship.get_name()} rotated {new_orient.lower()}.")
        else:
            self.__place_ship_cells(ship, original)
            messagebox.showerror("Invalid rotation", "Ship cannot rotate there because it would overlap or leave the grid.")
            self.status_var.set("Cannot rotate there: ship would overlap or leave the grid.")
        self.__draw_all()

    def __on_orientation_change(self, orientation):
        if self.phase != "placement" or self.selected_ship is None or self.drag_data is not None:
            return
        board = self.p1.get_plan_board()
        ship = self.selected_ship
        anchor_row, anchor_col = self.__ship_anchor(ship)
        old_orientation = self.__ship_orientation(ship)
        if old_orientation == orientation:
            return
        original = [(cell.get_x(), cell.get_y()) for cell in ship.get_cells_list()]
        if self.__can_place_ship(board, ship, anchor_row, anchor_col, orientation, ignore_ship=ship):
            self.__place_ship_strict(board, ship, anchor_row, anchor_col, orientation, ignore_ship=ship)
            self.status_var.set(f"{ship.get_name()} set to {orientation.lower()}.")
        else:
            self.__place_ship_cells(ship, original)
            self.current_orientation.set(old_orientation)
            messagebox.showerror("Invalid orientation", "Selected ship cannot use that orientation here.")
            self.status_var.set("Cannot rotate selected ship there.")
        self.__draw_all()

    def __update_drag_preview(self, event):
        rc = self.__grid_to_cell(event, self.PLAN_BOARD)
        if rc is None:
            return
        row, col = rc
        ship = self.drag_data["ship"]
        orient = self.drag_data["orientation"]
        preview_row = row - self.drag_data["offset_row"]
        preview_col = col - self.drag_data["offset_col"]
        preview_cells = self.__ship_cells_for_position(ship, preview_row, preview_col, orient)
        self.drag_data["preview_row"] = preview_row
        self.drag_data["preview_col"] = preview_col
        self.drag_data["preview_cells"] = preview_cells
        self.warning_cells = self.__warning_cells_for_preview(preview_cells)
        self.__draw_all()

    def __restore_dragged_ship(self):
        ship = self.drag_data["ship"]
        self.__place_ship_cells(ship, self.drag_data["original_cells"])

    def __place_ship_cells(self, ship, cells):
        ship.clear_cells()
        for row, col in cells:
            cell = self.p1.get_plan_board().get_cell(row, col)
            cell.set_ship(ship)
            cell.set_hit(False)
            ship.add_cell(cell)
        self.ship_orientations[ship] = self.__orientation_from_coords(cells)

    def __orientation_from_coords(self, cells):
        if len(cells) < 2:
            return "Horizontal"
        rows = {row for row, _ in cells}
        return "Horizontal" if len(rows) == 1 else "Vertical"

    def __warning_cells_for_preview(self, preview_cells):
        warnings = set()
        if not preview_cells:
            return warnings
        board = self.p1.get_plan_board()
        for row, col in preview_cells:
            for rr in range(row - 1, row + 2):
                for cc in range(col - 1, col + 2):
                    if 0 <= rr < board.get_num_rows() and 0 <= cc < board.get_num_cols():
                        other = board.get_cell(rr, cc).get_ship()
                        if other is not None:
                            warnings.add((row, col))
                            warnings.add((rr, cc))
        return warnings

    def __start_game(self):
        if self.phase != "placement":
            return
        if any(not ship.get_cells_list() for ship in self.p1.get_ships_list()):
            messagebox.showerror("Cannot start", "All ships must be placed before starting.")
            return
        self.phase = "battle"
        self.drag_data = None
        self.warning_cells = set()
        self.start_button.config(state=tk.DISABLED)
        self.randomise_button.config(state=tk.DISABLED)
        self.status_var.set("Battle started. Click the right grid to attack.")
        self.__draw_all()
        self.__start_idle_timer()

    def __on_attack_click(self, event):
        if self.phase != "battle" or self.current_player_index != 0:
            return
        rc = self.__grid_to_cell(event, self.ATTACK_BOARD)
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
                self.__flash_sunk(self.ATTACK_BOARD, result["sunk_cells"], 0)
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
                self.__flash_sunk(self.PLAN_BOARD, result["sunk_cells"], 0)
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

    def __draw_grid(self, board_name, title):
        origin_x, origin_y = self.__board_origin(board_name)
        canvas = self.game_canvas
        canvas.create_text(origin_x + self.BOARD_SIZE / 2, origin_y + 12, text=title, fill="white", font=("Arial", 12, "bold"))
        for i in range(10):
            x = origin_x + self.PADDING + i * self.CELL
            canvas.create_text(x + self.CELL / 2, origin_y + 25, text=chr(65 + i), fill="white")
            y = origin_y + self.PADDING + i * self.CELL
            canvas.create_text(origin_x + 15, y + self.CELL / 2, text=str(i), fill="white")
        for i in range(11):
            p = self.PADDING + i * self.CELL
            x1 = origin_x + self.PADDING
            y1 = origin_y + self.PADDING
            x2 = origin_x + self.PADDING + 10 * self.CELL
            y2 = origin_y + self.PADDING + 10 * self.CELL
            canvas.create_line(x1, origin_y + p, x2, origin_y + p, fill="#d9f6ff", width=1)
            canvas.create_line(origin_x + p, y1, origin_x + p, y2, fill="#d9f6ff", width=1)

    def __ship_groups(self, board):
        groups = {}
        for r in range(board.get_num_rows()):
            for c in range(board.get_num_cols()):
                cell = board.get_cell(r, c)
                if cell.has_ship():
                    ship = cell.get_ship()
                    groups.setdefault(ship.get_name(), {"ship": ship, "cells": []})["cells"].append((r, c, cell))
        return groups

    def __get_ship_photo(self, ship, horizontal):
        key = (ship.get_letter(), ship.get_size(), horizontal)
        if key in self.ship_image_cache:
            return self.ship_image_cache[key]

        filename = self.SHIP_IMAGE_FILES[ship.get_letter()]
        image_path = os.path.join(os.path.dirname(__file__), filename)
        image = Image.open(image_path).convert("RGBA")
        if horizontal:
            image = image.rotate(90, expand=True)
            image = image.resize((ship.get_size() * self.CELL, self.CELL), Image.Resampling.LANCZOS)
        else:
            image = image.resize((self.CELL, ship.get_size() * self.CELL), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(image)
        self.ship_image_cache[key] = photo
        self.ship_image_refs.append(photo)
        return photo

    def __get_ship_cell_photo(self, ship, horizontal, cell_index):
        key = (ship.get_letter(), ship.get_size(), horizontal, cell_index)
        if key in self.ship_image_cache:
            return self.ship_image_cache[key]

        filename = self.SHIP_IMAGE_FILES[ship.get_letter()]
        image_path = os.path.join(os.path.dirname(__file__), filename)
        image = Image.open(image_path).convert("RGBA")
        if horizontal:
            image = image.rotate(90, expand=True)
            image = image.resize((ship.get_size() * self.CELL, self.CELL), Image.Resampling.LANCZOS)
            image = image.crop((cell_index * self.CELL, 0, (cell_index + 1) * self.CELL, self.CELL))
        else:
            image = image.resize((self.CELL, ship.get_size() * self.CELL), Image.Resampling.LANCZOS)
            image = image.crop((0, cell_index * self.CELL, self.CELL, (cell_index + 1) * self.CELL))

        photo = ImageTk.PhotoImage(image)
        self.ship_image_cache[key] = photo
        self.ship_image_refs.append(photo)
        return photo

    def __draw_ship_icon(self, board_name, ship, cells):
        coords = []
        for cell_data in cells:
            coords.append((cell_data[0], cell_data[1]))
        self.__draw_ship_at_cells(board_name, ship, coords)

    def __draw_ship_at_cells(self, board_name, ship, coords):
        rows = sorted(r for r, _ in coords)
        cols = sorted(c for _, c in coords)
        min_r, max_r = rows[0], rows[-1]
        min_c, max_c = cols[0], cols[-1]
        x1, y1, _, _ = self.__cell_bounds(board_name, min_r, min_c)

        horizontal = max_r == min_r
        photo = self.__get_ship_photo(ship, horizontal)
        self.game_canvas.create_image(x1, y1, image=photo, anchor=tk.NW)

    def __draw_hit_ship_segments(self, board_name, ship, cells):
        coords = [(r, c, cell) for r, c, cell in cells]
        sorted_cells = sorted(coords, key=lambda item: (item[0], item[1]))
        rows = {r for r, _, _ in sorted_cells}
        horizontal = len(rows) == 1
        for index, (row, col, cell) in enumerate(sorted_cells):
            if not cell.is_hit():
                continue
            x1, y1, _, _ = self.__cell_bounds(board_name, row, col)
            photo = self.__get_ship_cell_photo(ship, horizontal, index)
            self.game_canvas.create_image(x1, y1, image=photo, anchor=tk.NW)

    def __draw_cell_overlay(self, board_name, row, col, color):
        x1, y1, x2, y2 = self.__cell_bounds(board_name, row, col, inset=1)
        self.game_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

    def __get_sunk_overlay_photo(self):
        key = ("sunk_overlay", self.CELL)
        if key in self.ship_image_cache:
            return self.ship_image_cache[key]
        image = Image.new("RGBA", (self.CELL - 2, self.CELL - 2), (255, 107, 107, 140))
        photo = ImageTk.PhotoImage(image)
        self.ship_image_cache[key] = photo
        self.ship_image_refs.append(photo)
        return photo

    def __draw_sunk_overlay(self, board_name, row, col):
        x1, y1, _, _ = self.__cell_bounds(board_name, row, col, inset=1)
        photo = self.__get_sunk_overlay_photo()
        self.game_canvas.create_image(x1, y1, image=photo, anchor=tk.NW)

    def __draw_warning_cells(self):
        for row, col in self.warning_cells:
            self.__draw_cell_overlay(self.PLAN_BOARD, row, col, "#808080")

    def __draw_drag_preview(self):
        if self.drag_data is None:
            return
        preview_cells = self.drag_data.get("preview_cells", [])
        if not preview_cells:
            return
        self.__draw_ship_at_cells(self.PLAN_BOARD, self.drag_data["ship"], preview_cells)
        self.__draw_warning_cells()

    def __draw_hits_and_misses(self, board_name, board):
        groups = self.__ship_groups(board)
        for group in groups.values():
            ship = group["ship"]
            cells = group["cells"]
            if ship.is_sunk():
                self.__draw_ship_icon(board_name, ship, cells)
                for r, c, _ in cells:
                    self.__draw_sunk_overlay(board_name, r, c)
                continue

            if board_name == self.PLAN_BOARD:
                self.__draw_ship_icon(board_name, ship, cells)
            elif any(cell.is_hit() for _, _, cell in cells):
                self.__draw_hit_ship_segments(board_name, ship, cells)

            for r, c, cell in cells:
                if cell.is_hit():
                    self.__draw_cell_overlay(board_name, r, c, "#8B0000")

        for r in range(board.get_num_rows()):
            for c in range(board.get_num_cols()):
                cell = board.get_cell(r, c)
                if cell.is_hit() and not cell.has_ship():
                    x1, y1, x2, y2 = self.__cell_bounds(board_name, r, c, inset=6)
                    self.game_canvas.create_oval(x1, y1, x2, y2, fill="white", outline="")

    def __draw_all(self):
        self.game_canvas.delete("all")
        self.__draw_background()
        self.__draw_grid(self.PLAN_BOARD, "Your planning board")
        self.__draw_grid(self.ATTACK_BOARD, "Attack board")
        self.__draw_hits_and_misses(self.PLAN_BOARD, self.p1.get_plan_board())
        self.__draw_hits_and_misses(self.ATTACK_BOARD, self.p1.get_attack_board())
        self.__draw_drag_preview()

    def __flash_sunk(self, board_name, cells, step):
        self.__draw_all()

    def __randomise_human_fleet(self):
        if self.phase != "placement":
            return
        self.drag_data = None
        self.warning_cells = set()
        self.__randomise_player_fleet(self.p1)
        self.current_ship_index = len(self.p1.get_ships_list())
        self.status_var.set("Fleet randomised. Drag ships or press Start.")
        self.__draw_all()

    def __randomise_player_fleet(self, player):
        player.clear_ship_positions()
        board = player.get_plan_board()
        ships = sorted(player.get_ships_list(), key=lambda item: item.get_size(), reverse=True)
        for ship in ships:
            if not self.__place_random_ship(board, ship, require_spacing=True):
                if not self.__place_random_ship(board, ship, require_spacing=False):
                    raise RuntimeError(f"Could not place {ship.get_name()}")

    def __place_random_ship(self, board, ship, require_spacing):
        for _ in range(500):
            orient = random.choice(["Horizontal", "Vertical"])
            row = random.randint(0, board.get_num_rows() - 1)
            col = random.randint(0, board.get_num_cols() - 1)
            if require_spacing:
                if board.place_ship_with_spacing(ship, row, col, orient):
                    self.ship_orientations[ship] = orient
                    return True
            elif board.place_ship(ship, row, col, orient):
                self.ship_orientations[ship] = orient
                return True
        return False

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
