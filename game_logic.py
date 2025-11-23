import time
from tkinter import messagebox, Toplevel
from board import Board
class Game:
    def __init__(self, board_obj, fm, ui, post_game_callback):
        self.board = board_obj; self.fm = fm; self.ui = ui
        self.post_game_callback = post_game_callback
        self.start_time = None; self.game_over = False
        self.current_save_slot = None
        self.clicks = 0; self.first_click = None
    def start(self, resume=False, elapsed_before=0):
        self.game_over = False; self.ui.bind(self)
        if resume:
            self.start_time = time.time() - int(elapsed_before)
            self.ui.set_timer(elapsed_before); self.board.placed = True
        else:
            self.board.placed = False; self.start_time = None
        self.ui.update_counters(len(self.board.flagged), self.board.mines)
        self.ui.set_clicks(self.clicks)
    def get_elapsed(self):
        if self.start_time is None: return 0
        return int(time.time() - self.start_time)
    def _ensure_timer(self):
        if self.start_time is None:
            self.start_time = time.time(); self.ui.start_timer(self.get_elapsed)
    def on_left(self, r, c):
        if self.game_over: return
        if not getattr(self.board, "placed", False):
            self.board.place_mines_avoiding((r, c)); self.board.placed = True
            self.first_click = (r, c); self._ensure_timer()
        else:
            self._ensure_timer()
        self.clicks += 1; self.ui.set_clicks(self.clicks)
        if self.board.grid[r][c] == "M":
            self.board.revealed[r][c] = True
            self.ui.reveal_cell(r, c, "M"); self._lose(); return
        cells = self.board.reveal(r, c)
        for rr, cc, val in cells: self.ui.reveal_cell(rr, cc, val)
        if self.board.check_win(): self._win()
    def on_right(self, r, c):
        if self.game_over: return
        self.clicks += 1; self.ui.set_clicks(self.clicks)
        res = self.board.toggle_flag(r, c)
        if res is None: return
        self.ui.set_flag(r, c, res)
        self.ui.update_counters(len(self.board.flagged), self.board.mines)
        if self.board.check_win(): self._win()
    def on_middle(self, r, c): pass
    def _end_and_cleanup_slot(self):
        if getattr(self, "current_save_slot", None):
            try: self.fm.delete_slot_file(self.current_save_slot)
            except Exception: pass
    def _win(self):
        self.game_over = True
        ela = self.get_elapsed()
        nam = self.ui.get_player_name()
        self.fm.save_score(nam, ela, self.board.rows, self.board.cols, self.board.mines, "win", clicks=self.clicks, seed=self.board.seed)
        self._end_and_cleanup_slot()
        if callable(self.post_game_callback): self.post_game_callback("win", ela, self.clicks, None)
        try: self.ui.close()
        except Exception: pass
    def _lose(self):
        self.game_over = True
        ela = self.get_elapsed()
        for r, c, _ in self.board.reveal_all_mines(): self.ui.reveal_mine(r, c)
        nam = self.ui.get_player_name()
        self.fm.save_score(nam, ela, self.board.rows, self.board.cols, self.board.mines, "lose", clicks=self.clicks, seed=self.board.seed)
        self._end_and_cleanup_slot()
        if callable(self.post_game_callback): self.post_game_callback("lose", ela, self.clicks, None)
        try: self.ui.close()
        except Exception: pass
    def save_prompt(self):
        """Synchronous save dialog: blocks until user picks a slot or closes the dialog."""
        prm = Toplevel(); prm.title("Save - Choose Slot")
        Tk = __import__("tkinter"); Lb = getattr(Tk, "Label"); Bt = getattr(Tk, "Button")
        Lb(prm, text="Choose slot (1-3):").grid(row=0, column=0, columnspan=3, pady=6)
        def do_save(slt):
            if self.fm.slot_exists(slt):
                if not messagebox.askyesno("Overwrite?", f"Slot {slt} is occupied. Overwrite?"): return
            ela = self.get_elapsed()
            if self.board.seed is None: self.board.seed = 0
            self.fm.write_slot(slt, self.board, ela)
            self.current_save_slot = slt
            messagebox.showinfo("Saved", f"Game saved to slot {slt}."); prm.destroy()
        for i in range(1, 4):
            sts = "Empty" if not self.fm.slot_exists(i) else "Occupied"
            Bt(prm, text=f"Slot {i}\n({sts})", width=12, command=lambda s=i: do_save(s)).grid(row=1, column=i - 1, padx=6, pady=6)
        prm.transient(self.ui.root); prm.grab_set(); prm.focus_force(); prm.wait_window()
