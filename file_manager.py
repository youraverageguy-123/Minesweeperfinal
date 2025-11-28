import os
from tkinter import messagebox, Toplevel, ttk, Frame, Label
from tkinter import LEFT, RIGHT, BOTH, Y, VERTICAL, Scrollbar
class FileManager:
    #Handles saving/loading of game data, score lodging, save-slot management, and leaderboard UI generation 
    def __init__(self, score_file="scores.csv", saves_dir="saves"):
        #Setup file paths for score and save slots
        self.score_file = score_file; self.saves_dir = saves_dir
        os.makedirs(self.saves_dir, exist_ok=True)
        #Pre generate paths for slots slot1.txt, slot2.txt, slot3.txt
        self.slot_files = [os.path.join(self.saves_dir, f"slot{i}.txt") for i in range(1, 4)]
    def save_score(self, name, elapsed, rows, cols, mines, result, clicks=None, seed=None):
        #Append a player result entry score to CSV files scores, which is used after the game ends whehter it is a win or loss
        sdl = "?" if seed is None else str(seed)
        ckv = "?" if clicks is None else str(clicks)
        try:
            with open(self.score_file, "a") as f:
                f.write(f"{name},{elapsed},{ckv},{rows},{cols},{mines},{result},{sdl}\n")
        except Exception: pass
    def load_scores(self):
        #Read and parse the stored scores from the score file, return as a list of dicts
        if not os.path.exists(self.score_file): return []
        out = []
        try:
            with open(self.score_file, "r") as f:
                for ln in f:
                    pts = [p.strip() for p in ln.strip().split(",")]
                    if len(pts) < 7: continue
                    #Extract score fields with safe fallback values
                    nam = pts[0]
                    ela = pts[1] if len(pts) > 1 else "?"
                    clk = pts[2] if len(pts) > 2 else "?"
                    rws = pts[3] if len(pts) > 3 else "?"
                    cls = pts[4] if len(pts) > 4 else "?"
                    mns = pts[5] if len(pts) > 5 else "?"
                    res = pts[6] if len(pts) > 6 else "?"
                    sdl = pts[7] if len(pts) > 7 else "?"
                    out.append({"name": nam, "elapsed": ela, "clicks": clk, "rows": rws, "cols": cls, "mines": mns, "result": res, "seed": sdl})
        except Exception: return out
        return out
    def show_leaderboard(self, parent):
        #Create a leaderboard window with two tabs: wins and losses, with each player name, time, difficulty, and clicks and clicking on a row shows detailed history of that player
        scs = self.load_scores()
        if not scs:
            messagebox.showinfo("Leaderboard", "No scores yet: Be ready to be the first loser."); return
        #Separate wins and losses per player
        lwn = {}; lls = {}; pls = set()
        for s in scs:
            nam = s["name"]; pls.add(nam)
            res = s.get("result", "").lower()
            if res == "win": lwn[nam] = s
            elif res in ("lose", "loss"): lls[nam] = s
        wls = list(lwn.values()); los = list(lls.values())
        #Helper to convert elapsed to int for sorting
        def tky(e):
            t = e.get("elapsed", "?")
            if isinstance(t, str) and t.isdigit(): return int(t)
            if isinstance(t, int): return int(t)
            return 999999
        #Sort both lists by elapsed time
        wls.sort(key=tky); los.sort(key=tky)
        #Create leaderboard window
        winw = Toplevel(parent); winw.title("Leaderboard")
        winw.geometry("760x420"); winw.minsize(520, 320)
        nbk = ttk.Notebook(winw); nbk.pack(fill=BOTH, expand=True, padx=6, pady=6)
        #Columns to display in tree view
        cols = ("player", "time", "difficulty", "clicks")
        #Helper to create each leaderboard tab
        def mk_tab(ttl, dat, is_win):
            frm = ttk.Frame(nbk); nbk.add(frm, text=ttl)
            tr = ttk.Treeview(frm, columns=cols, show="headings")
            #Column headers
            tr.heading("player", text="Player")
            tr.heading("time", text="Time (s)")
            tr.heading("difficulty", text="Difficulty [rowsxcols,mines]")
            #Column width setup
            tr.heading("clicks", text="Clicks")
            tr.column("player", width=220, anchor="w")
            tr.column("time", width=80, anchor="center")
            tr.column("difficulty", width=320, anchor="center")
            tr.column("clicks", width=80, anchor="center")
            #Add vertical scrollbar
            vsb = Scrollbar(frm, orient=VERTICAL, command=tr.yview)
            tr.configure(yscrollcommand=vsb.set)
            vsb.pack(side=RIGHT, fill=Y); tr.pack(side=LEFT, fill=BOTH, expand=True)
            #Insert row entries
            for i, s in enumerate(dat):
                nam = s["name"]; t = s.get("elapsed", "?")
                dff = f"[{s.get('rows','?')}x{s.get('cols','?')},{s.get('mines','?')}]"
                clk = s.get("clicks", "?"); iid = f"{ttl}_{i}_{nam}"
                tr.insert("", "end", iid=iid, values=(nam, t, dff, clk))
            #Show a detailed per player history on row click
            def on_clk(ev):
                row = tr.identify_row(ev.y)
                if not row: return
                ply = tr.item(row, "values")[0]
                cat = "win" if is_win else "lose"
                #Filter scores for the selected player's category
                hist = [h for h in scs if h["name"] == ply and h.get("result", "").lower() == cat]
                if not hist:
                    messagebox.showinfo("History", f"No {cat}s found for {ply}."); return
                #Sort their runs by elapsed time
                hist.sort(key=lambda h: int(h["elapsed"]) if isinstance(h.get("elapsed"), str) and h["elapsed"].isdigit() else 999999)
                #Create history window
                hw = Toplevel(winw); hw.title(f"{ply} — {ttl} history"); hw.geometry("620x320")
                tr2 = ttk.Treeview(hw, columns=("idx", "time", "clicks", "difficulty", "seed"), show="headings")
                #Set headers
                tr2.heading("idx", text="#"); tr2.heading("time", text="Time(s)")
                tr2.heading("clicks", text="Clicks"); tr2.heading("difficulty", text="Difficulty")
                tr2.heading("seed", text="Seed")
                #Set column widths
                tr2.column("idx", width=40, anchor="center")
                tr2.column("time", width=80, anchor="center")
                tr2.column("clicks", width=80, anchor="center")
                tr2.column("difficulty", width=300, anchor="w")
                tr2.column("seed", width=80, anchor="center")
                tr2.pack(fill=BOTH, expand=True, padx=8, pady=8)
                #Insert history rows
                for i, h in enumerate(hist, start=1):
                    dff = f"[{h.get('rows','?')}x{h.get('cols','?')},{h.get('mines','?')}]"
                    tr2.insert("", "end", values=(i, h.get("elapsed","?"), h.get("clicks","?"), dff, h.get("seed","?")))
                hw.transient(winw); hw.grab_set(); hw.focus_force(); hw.update_idletasks()
            tr.bind("<ButtonRelease-1>", on_clk)
            return tr
        #Create both tabs
        mk_tab("Wins", wls, True); mk_tab("Losses", los, False)
        winw.transient(parent); winw.grab_set(); winw.focus_force(); winw.update_idletasks()
    def write_slot(self, slot, board_obj, elapsed):
        #Save a game snapshot into a slot file, which stores board dimensions, mine positions, revealed cells, flagged cells, elapsed time, and seed
        pth = self.slot_files[slot - 1]
        sdl = board_obj.seed if board_obj.seed is not None else 0
        with open(pth, "w") as f:
            f.write(f"{board_obj.rows} {board_obj.cols} {board_obj.mines}\n")
            f.write(f"{int(elapsed)}\n"); f.write(f"{int(sdl)}\n")
            #Save grid (M or number as char)
            for rw in board_obj.grid: f.write("".join(rw) + "\n")
            #Save revealed matrix(1 for revealed, 0 for hidden)
            for rw in board_obj.revealed: f.write("".join("1" if x else "0" for x in rw) + "\n")
            #Saved flagged cells
            flg = ";".join(f"{r},{c}" for (r, c) in board_obj.flagged)
            f.write(flg + "\n")
    def read_slot(self, slot):
        #Load saved game state from a slot file, return dict with all board data or None if slot is empty or invalid
        pth = self.slot_files[slot - 1]
        if not os.path.exists(pth): return None
        with open(pth, "r") as f: lns = [l.rstrip("\n") for l in f.readlines()]
        
        if len(lns) < 3: return None
        hdr = lns[0].split()
        if len(hdr) != 3 or not all(h.isdigit() for h in hdr): return None
        rows, cols, mines = map(int, hdr); ela = int(lns[1]); sdl = int(lns[2])
        #Validate we have enough lines for grid and revealed
        if len(lns) < 3 + rows + rows: return None
        #Load grid 
        grd = [list(lns[3 + r]) for r in range(rows)]
        rs = 3 + rows
        #Load revealed matrix
        rev = [[c == "1" for c in lns[rs + r]] for r in range(rows)]
        #Flagged cells
        fl_ln = lns[rs + rows] if len(lns) > rs + rows else ""
        flg = set()
        if fl_ln:
            for pr in fl_ln.split(";"):
                if "," in pr:
                    prr, prc = pr.split(",")
                    if prr.lstrip("-").isdigit() and prc.lstrip("-").isdigit(): flg.add((int(prr), int(prc)))
        return {"rows": rows, "cols": cols, "mines": mines, "grid": grd, "revealed": rev, "flagged": flg, "elapsed": ela, "seed": sdl}
    def slot_exists(self, slot): 
        #Check whether a save slot file exists for the given slots
        return os.path.exists(self.slot_files[slot - 1])
    def delete_slot_file(self, slot):
        #Delete a specific slot file
        pth = self.slot_files[slot - 1]
        if os.path.exists(pth): os.remove(pth)
    def delete_all_slots(self):
        #Delete all slot files
        for pth in self.slot_files:
            if os.path.exists(pth): os.remove(pth)
    def clear_scores(self):
        #Remove the score file after user confirmation which clears the leaderboard
        if os.path.exists(self.score_file):
            if messagebox.askyesno("Confirm", "Clear leaderboard?"):
                os.remove(self.score_file); messagebox.showinfo("Done", "Leaderboard cleared.")
        else:
            messagebox.showinfo("Info", "Leaderboard already empty.")

