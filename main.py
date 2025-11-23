# main.py
import tkinter as tk
from tkinter import messagebox
import sys
from board import Board
from game_logic import Game
from file_manager import FileManager
#Board paramters (default)
DEFAULT_ROWS, DEFAULT_COLS, DEFAULT_MINES = 9, 9, 15
#Difficulties presets
PRESETS = {"Easy": (9, 9, 10), "Normal": (16, 16, 40), "Hard": (16, 30, 99)}
class BoardUI:
    #Handles all UI elements of Tkinter like grid buttons, timers, flags, save button
    def __init__(self, root, pnc):
        self.root = root
        self.pnc = pnc
        self.btns = {}
        self._timer_job = None
        self._elapsed_fn = None
        self._cell_font = ("Helvetica", 12, "bold")
        self.num_color = {"1": "#0000FF","2": "#008000","3": "#FF0000","4": "#000080","5": "#800000","6": "#008B8B","7": "#000000","8": "#808080"}
    def build(self, rows, cols, mines):
        #Build the entire GUI again, used in save or load game, and clear old widgets and create new fresh buttons
        self.rows, self.cols, self.mines = rows, cols, mines
        #Clears old widgets
        for w in list(self.root.grid_slaves()): w.grid_forget()
        #Configure rows and columns 
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)
        #Headers of timer, flags, clicks
        hdr = tk.Frame(self.root); hdr.grid(row=0, column=0, pady=(6, 2))
        stf = ("Arial", 12, "bold")
        self.lbl_time = tk.Label(hdr, text="Time: 0s", font=stf); self.lbl_time.pack(side="left", padx=(4, 8))
        self.lbl_flags = tk.Label(hdr, text=f"Flags: 0/{mines}", font=stf); self.lbl_flags.pack(side="left", padx=(0, 8))
        self.lbl_clicks = tk.Label(hdr, text="Clicks: 0", font=stf); self.lbl_clicks.pack(side="left", padx=(0, 4))
        #Container for board
        ctr = tk.Frame(self.root); ctr.grid(row=1, column=0)
        hld = tk.Frame(ctr); hld.grid(row=0, column=0)
        grd = tk.Frame(hld); grd.grid(row=0, column=0)
        self.btns = {}; gp = 1 #gap between buttons
        #Create buttons grid
        for r in range(rows):
            grd.rowconfigure(r, weight=0)
            for c in range(cols):
                grd.columnconfigure(c, weight=0)
                b = tk.Button(grd, text="", width=2, height=1, relief="raised", bd=2, bg="#e9e9e9", activebackground="#e9e9e9", font=self._cell_font)
                b.grid(row=r, column=c, padx=gp, pady=gp, ipadx=0, ipady=0)
                #Bind mouse events to button
                b.bind("<Button-1>", lambda ev, rr=r, cc=c: self._on_left(rr, cc))
                b.bind("<Button-3>", lambda ev, rr=r, cc=c: self._on_right(rr, cc))
                b.bind("<Button-2>", lambda ev, rr=r, cc=c: self._on_middle(rr, cc))
                b.bind("<Control-Button-1>", lambda ev, rr=r, cc=c: self._on_right(rr, cc))
                b.config(disabledforeground="black")
                self.btns[(r, c)] = b
        #Bottom controls
        ctl = tk.Frame(self.root); ctl.grid(row=2, column=0, pady=(6, 6))
        tk.Button(ctl, text="Save", width=10, command=self._on_save).pack(side="left", padx=6)
    #Binds UI logic to game logic
    def bind(self, game): self._game = game
    def get_player_name(self): return self.pnc()
    #Click handlers 
    def _on_left(self, r, c):
        if hasattr(self, "_game"): self._game.on_left(r, c)
    def _on_right(self, r, c):
        if hasattr(self, "_game"): self._game.on_right(r, c)
    def _on_middle(self, r, c):
        if hasattr(self, "_game"): self._game.on_middle(r, c)
    #Display updates
    def reveal_cell(self, r, c, val):
        #Visually reveal one cell. Color, number, mine, bg updates
        b = self.btns.get((r, c))
        if not b: return
        b.config(relief="sunken", state="disabled")
        if val == "M": b.config(text="M", fg="black", bg="#ff4d4d", disabledforeground="black")
        elif val == "0": b.config(text="", bg="#dff7f9")
        else:
            clr = self.num_color.get(str(val), "black")
            b.config(text=str(val), fg=clr, disabledforeground=clr, bg="#dff7f9")
    def reveal_mine(self, r, c): self.reveal_cell(r, c, "M")
    #Set or unset flag on a cell visually
    def set_flag(self, r, c, flg):
        b = self.btns.get((r, c))
        if not b: return
        if flg: b.config(text="F", fg="#C00000", bg="#FFF3D9", state="normal")
        else: b.config(text="", fg="black", bg="#e9e9e9", state="normal")
    def update_counters(self, flc, mns): self.lbl_flags.config(text=f"Flags: {flc}/{mns}")
    #Time handling
    def start_timer(self, elf):
        self._elapsed_fn = elf
        self._tick()
    def _tick(self):
        if not self._elapsed_fn: return
        self.lbl_time.config(text=f"Time: {self._elapsed_fn()}s")
        self._timer_job = self.root.after(1000, self._tick)
    def set_timer(self, val): self.lbl_time.config(text=f"Time: {int(val)}s")
    def set_clicks(self, n): self.lbl_clicks.config(text=f"Clicks: {n}")
    #Close the UI
    def close(self):
        try:
            if getattr(self, "_timer_job", None): self.root.after_cancel(self._timer_job)
            self.root.destroy()
        except Exception: pass
    def _on_save(self):
        if hasattr(self, "_game"): self._game.save_prompt()
#Game startup and main menu
def start_game(rows, cols, mines, name, fm, slot_data=None, slot_index=None):
    #Entry to start of the game and handles window creation, loading saved games, building UI and binding logic
    grt = tk.Tk()
    grt.title("Minesweeper")
    grt.resizable(False, False)
    #Create UI
    ui = BoardUI(grt, lambda: name)
    #Create board new or old saved ones
    if slot_data is None:
        brd = Board(rows, cols, mines)
    else:
        brd = Board(slot_data["rows"], slot_data["cols"], slot_data["mines"], seed=slot_data.get("seed"), grid=slot_data.get("grid"), revealed=slot_data.get("revealed"), flagged=slot_data.get("flagged"))
    #Callback for end of game
    def post_game_cb(res, ela, clk, _un):
        e3bv = brd.compute_e3bv(first_click=getattr(game, "first_click", None))
        ttl = "Victory!" if res == "win" else "Game Over"
        msg = f"{'You won!' if res == 'win' else 'You lost!'}\nTime: {ela}s\nClicks: {clk}\ne3BV: {e3bv}\n\nGo to main menu? (Yes → main menu, No → exit)"
        ans = messagebox.askyesno(ttl, msg, parent=grt)
        try: grt.destroy()
        except Exception: pass
        if ans: main_menu(prefill_name=name)
        else: sys.exit(0)
    #Create game logic
    game = Game(brd, fm, ui, post_game_cb)
    #When loading, store which slot is being used
    if slot_index is not None: game.current_save_slot = slot_index
    #Build UI and bing game logic
    ui.build(brd.rows, brd.cols, brd.mines)
    ui.bind(game)
    #Restore loaded game state visually 
    if slot_data is not None:
        ui.set_timer(slot_data.get("elapsed", 0))
        for r in range(brd.rows):
            for c in range(brd.cols):
                if brd.revealed[r][c]: ui.reveal_cell(r, c, brd.grid[r][c])
        for (r, c) in sorted(brd.flagged): ui.set_flag(r, c, True)
    #Handle window close event
    def on_close():
        if game.game_over:
            try: ui.close()
            except Exception: pass
            try: grt.destroy()
            except Exception: pass
            return
        ans = messagebox.askyesnocancel("Exit", "Save game before exiting?\nYes = Save & Exit\nNo = Exit without saving\nCancel = Return to game", parent=grt)
        if ans is None: return
        if ans is True:
            game.save_prompt()
            try: ui.close()
            except Exception: pass
            try: grt.destroy()
            except Exception: pass
            return
        else:
            try: ui.close()
            except Exception: pass
            try: grt.destroy()
            except Exception: pass
            return
    grt.protocol("WM_DELETE_WINDOW", on_close)
    #Start the game
    game.start(resume=(slot_data is not None), elapsed_before=(slot_data.get("elapsed", 0) if slot_data else 0))
    grt.mainloop()
#Main menuu UI and logic 
def main_menu(prefill_name=None):
#Draw main menu with name entry,custom board, default start, presets, load slot, leaderboard, clear scores, exit
    fm = FileManager()
    win = tk.Tk()
    win.title("Minesweeper - Menu")
    container = tk.Frame(win)
    container.pack()
    tk.Label(container, text="Minesweeper", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=(12, 8))
    #Form for main and board size
    form = tk.Frame(container)
    form.grid(row=1, column=0, pady=(2, 8))
    tk.Label(form, text="Name:", width=8, anchor="e").grid(row=0, column=0, padx=6, pady=4)
    entry_name = tk.Entry(form, width=18)
    entry_name.grid(row=0, column=1, padx=6, pady=4)
    if prefill_name:
        entry_name.insert(0, prefill_name)
    else:
        entry_name.insert(0, "Player1")
    tk.Label(form, text="Rows:", width=8, anchor="e").grid(row=1, column=0, padx=6, pady=2)
    entry_rows = tk.Entry(form, width=6)
    entry_rows.grid(row=1, column=1, padx=6, pady=2)
    entry_rows.insert(0, str(DEFAULT_ROWS))
    tk.Label(form, text="Cols:", width=8, anchor="e").grid(row=2, column=0, padx=6, pady=2)
    entry_cols = tk.Entry(form, width=6)
    entry_cols.grid(row=2, column=1, padx=6, pady=2)
    entry_cols.insert(0, str(DEFAULT_COLS))
    tk.Label(form, text="Mines:", width=8, anchor="e").grid(row=3, column=0, padx=6, pady=2)
    entry_mines = tk.Entry(form, width=6)
    entry_mines.grid(row=3, column=1, padx=6, pady=2)
    entry_mines.insert(0, str(DEFAULT_MINES))
    #Helper to validate name entry
    def valid_name():
        n = entry_name.get().strip()
        if not n:
            messagebox.showerror("Missing name", "Please enter your name.")
            return None
        return n
    #Custom board start
    def start_custom():
        n = valid_name()
        if not n:
            return
        if not (entry_rows.get().isdigit() and entry_cols.get().isdigit() and entry_mines.get().isdigit()):
            messagebox.showerror("Error", "Row/Column/Mine values must be numeric.")
            return
        r = int(entry_rows.get()); c = int(entry_cols.get()); m = int(entry_mines.get())
        if m >= r * c:
            messagebox.showerror("Error", "Too many mines for this board.")
            return
        win.destroy()
        start_game(r, c, m, n, fm)
    #Default board start
    def start_default():
        n = valid_name()
        if not n:
            return
        win.destroy()
        start_game(DEFAULT_ROWS, DEFAULT_COLS, DEFAULT_MINES, n, fm)
    #Buttons grp
    btns = tk.Frame(container)
    btns.grid(row=2, column=0, pady=(4, 6))
    tk.Button(btns, text="Start (Custom)", width=16, command=start_custom).grid(row=0, column=0, padx=8)
    tk.Button(btns, text="Default (9×9, 15)", width=16, command=start_default).grid(row=0, column=1, padx=8)
    #Presets
    preset_label = tk.Label(container, text="Quick Presets:")
    preset_label.grid(row=3, column=0, pady=(6, 4))
    preset_frame = tk.Frame(container)
    preset_frame.grid(row=4, column=0)
    def start_preset(preset_tuple):
        n = valid_name()
        if not n:
            return
        r, c, m = preset_tuple
        win.destroy()
        start_game(r, c, m, n, fm)
    for i, (k, v) in enumerate(PRESETS.items()):
        tk.Button(preset_frame, text=k, width=10, command=(lambda p=v: start_preset(p))).grid(row=0, column=i, padx=6)
    #Lower menu buttons
    lower = tk.Frame(container)
    lower.grid(row=5, column=0, pady=(6, 6))
    tk.Button(lower, text="Load Slot", width=12, command=lambda: load_slot_prompt(win, fm, entry_name)).grid(row=0, column=0, padx=6)
    tk.Button(lower, text="Leaderboard", width=12, command=lambda: fm.show_leaderboard(win)).grid(row=0, column=1, padx=6)
    tk.Button(lower, text="Clear Scores", width=12, command=fm.clear_scores).grid(row=0, column=2, padx=6)
    tk.Button(container, text="Exit", width=12, command=win.destroy).grid(row=6, column=0, pady=(6, 8))
    info = tk.Label(
        container,
        text="e3BV = Effective 3BV, a measure of board complexity.\nHigher e3BV indicates a more challenging game.\n0-10: Easy, 11-25: Medium, 25-40: Tricky, 40+: Hard",
        font=("Arial", 9),
        fg = "#555555",
        justify="center"
    )
    info.grid(row =7, column =0, pady =(4,8))

    
    #Center window 
    win.update_idletasks()
    w = win.winfo_reqwidth(); h = win.winfo_reqheight()
    win.geometry(f"{w+6}x{h+6}")
    win.resizable(False, False)
    win.mainloop()
#Load save prompt
def load_slot_prompt(win, fm, entry_widget):
    #Pop up display to load a save slot, and display slot status (Empty/Occupied) for slots 1,2 and 3
    n = entry_widget.get().strip()
    if not n:
        messagebox.showerror("Missing name", "Enter your name")
        return
    dlg = tk.Toplevel(win)
    dlg.title("Load Slot")
    tk.Label(dlg, text="Choose slot to load:").grid(row=0, column=0, columnspan=3, pady=6)
    def do_load(slot):
        #If slot empty 
        if not fm.slot_exists(slot):
            messagebox.showinfo("Load", f"Slot {slot} is empty.")
            return
        data = fm.read_slot(slot)
        if data is None:
            messagebox.showerror("Load", "Slot appears corrupted.")
            return
        dlg.destroy()
        win.destroy()
        start_game(data["rows"], data["cols"], data["mines"], n, fm, slot_data=data, slot_index=slot)
    #Create slot buttons from 1 to 3
    for i in range(1, 4):
        status = "Empty" if not fm.slot_exists(i) else "Occupied"
        tk.Button(dlg, text=f"Slot {i}\n({status})", width=12, command=lambda s=i: do_load(s)).grid(row=1, column=i-1, padx=6, pady=6)
#Entry point
if __name__ == "__main__":
    main_menu()
