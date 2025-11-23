import os
from tkinter import messagebox, Toplevel, ttk, Frame, Label
from tkinter import LEFT, RIGHT, BOTH, Y, VERTICAL, Scrollbar
class FileManager:
    def __init__(self, score_file="scores.csv", saves_dir="saves"):
        self.score_file = score_file; self.saves_dir = saves_dir
        os.makedirs(self.saves_dir, exist_ok=True)
        self.slot_files = [os.path.join(self.saves_dir, f"slot{i}.txt") for i in range(1, 4)]
    def save_score(self, name, elapsed, rows, cols, mines, result, clicks=None, seed=None):
        sdl = "?" if seed is None else str(seed)
        ckv = "?" if clicks is None else str(clicks)
        try:
            with open(self.score_file, "a") as f:
                f.write(f"{name},{elapsed},{ckv},{rows},{cols},{mines},{result},{sdl}\n")
        except Exception: pass
    def load_scores(self):
        if not os.path.exists(self.score_file): return []
        out = []
        try:
            with open(self.score_file, "r") as f:
                for ln in f:
                    pts = [p.strip() for p in ln.strip().split(",")]
                    if len(pts) < 7: continue
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
        scs = self.load_scores()
        if not scs:
            messagebox.showinfo("Leaderboard", "No scores yet — be the first loser."); return
        lwn = {}; lls = {}; pls = set()
        for s in scs:
            nam = s["name"]; pls.add(nam)
            res = s.get("result", "").lower()
            if res == "win": lwn[nam] = s
            elif res in ("lose", "loss"): lls[nam] = s
        wls = list(lwn.values()); los = list(lls.values())
        def tky(e):
            t = e.get("elapsed", "?")
            if isinstance(t, str) and t.isdigit(): return int(t)
            if isinstance(t, int): return int(t)
            return 999999
        wls.sort(key=tky); los.sort(key=tky)
        winw = Toplevel(parent); winw.title("Leaderboard")
        winw.geometry("760x420"); winw.minsize(520, 320)
        nbk = ttk.Notebook(winw); nbk.pack(fill=BOTH, expand=True, padx=6, pady=6)
        cols = ("player", "time", "difficulty", "clicks")
        def mk_tab(ttl, dat, is_win):
            frm = ttk.Frame(nbk); nbk.add(frm, text=ttl)
            tr = ttk.Treeview(frm, columns=cols, show="headings")
            tr.heading("player", text="Player")
            tr.heading("time", text="Time (s)")
            tr.heading("difficulty", text="Difficulty [rowsxcols,mines]")
            tr.heading("clicks", text="Clicks")
            tr.column("player", width=220, anchor="w")
            tr.column("time", width=80, anchor="center")
            tr.column("difficulty", width=320, anchor="center")
            tr.column("clicks", width=80, anchor="center")
            vsb = Scrollbar(frm, orient=VERTICAL, command=tr.yview)
            tr.configure(yscrollcommand=vsb.set)
            vsb.pack(side=RIGHT, fill=Y); tr.pack(side=LEFT, fill=BOTH, expand=True)
            for i, s in enumerate(dat):
                nam = s["name"]; t = s.get("elapsed", "?")
                dff = f"[{s.get('rows','?')}x{s.get('cols','?')},{s.get('mines','?')}]"
                clk = s.get("clicks", "?"); iid = f"{ttl}_{i}_{nam}"
                tr.insert("", "end", iid=iid, values=(nam, t, dff, clk))
            def on_clk(ev):
                row = tr.identify_row(ev.y)
                if not row: return
                ply = tr.item(row, "values")[0]
                cat = "win" if is_win else "lose"
                hist = [h for h in scs if h["name"] == ply and h.get("result", "").lower() == cat]
                if not hist:
                    messagebox.showinfo("History", f"No {cat}s found for {ply}."); return
                hist.sort(key=lambda h: int(h["elapsed"]) if isinstance(h.get("elapsed"), str) and h["elapsed"].isdigit() else 999999)
                hw = Toplevel(winw); hw.title(f"{ply} — {ttl} history"); hw.geometry("620x320")
                tr2 = ttk.Treeview(hw, columns=("idx", "time", "clicks", "difficulty", "seed"), show="headings")
                tr2.heading("idx", text="#"); tr2.heading("time", text="Time(s)")
                tr2.heading("clicks", text="Clicks"); tr2.heading("difficulty", text="Difficulty")
                tr2.heading("seed", text="Seed")
                tr2.column("idx", width=40, anchor="center")
                tr2.column("time", width=80, anchor="center")
                tr2.column("clicks", width=80, anchor="center")
                tr2.column("difficulty", width=300, anchor="w")
                tr2.column("seed", width=80, anchor="center")
                tr2.pack(fill=BOTH, expand=True, padx=8, pady=8)
                for i, h in enumerate(hist, start=1):
                    dff = f"[{h.get('rows','?')}x{h.get('cols','?')},{h.get('mines','?')}]"
                    tr2.insert("", "end", values=(i, h.get("elapsed","?"), h.get("clicks","?"), dff, h.get("seed","?")))
                hw.transient(winw); hw.grab_set(); hw.focus_force(); hw.update_idletasks()
            tr.bind("<ButtonRelease-1>", on_clk)
            return tr
        mk_tab("Wins", wls, True); mk_tab("Losses", los, False)
        winw.transient(parent); winw.grab_set(); winw.focus_force(); winw.update_idletasks()
    def write_slot(self, slot, board_obj, elapsed):
        pth = self.slot_files[slot - 1]
        sdl = board_obj.seed if board_obj.seed is not None else 0
        with open(pth, "w") as f:
            f.write(f"{board_obj.rows} {board_obj.cols} {board_obj.mines}\n")
            f.write(f"{int(elapsed)}\n"); f.write(f"{int(sdl)}\n")
            for rw in board_obj.grid: f.write("".join(rw) + "\n")
            for rw in board_obj.revealed: f.write("".join("1" if x else "0" for x in rw) + "\n")
            flg = ";".join(f"{r},{c}" for (r, c) in board_obj.flagged)
            f.write(flg + "\n")
    def read_slot(self, slot):
        pth = self.slot_files[slot - 1]
        if not os.path.exists(pth): return None
        with open(pth, "r") as f: lns = [l.rstrip("\n") for l in f.readlines()]
        if len(lns) < 3: return None
        hdr = lns[0].split()
        if len(hdr) != 3 or not all(h.isdigit() for h in hdr): return None
        rows, cols, mines = map(int, hdr); ela = int(lns[1]); sdl = int(lns[2])
        if len(lns) < 3 + rows + rows: return None
        grd = [list(lns[3 + r]) for r in range(rows)]
        rs = 3 + rows
        rev = [[c == "1" for c in lns[rs + r]] for r in range(rows)]
        fl_ln = lns[rs + rows] if len(lns) > rs + rows else ""
        flg = set()
        if fl_ln:
            for pr in fl_ln.split(";"):
                if "," in pr:
                    prr, prc = pr.split(",")
                    if prr.lstrip("-").isdigit() and prc.lstrip("-").isdigit(): flg.add((int(prr), int(prc)))
        return {"rows": rows, "cols": cols, "mines": mines, "grid": grd, "revealed": rev, "flagged": flg, "elapsed": ela, "seed": sdl}
    def slot_exists(self, slot): return os.path.exists(self.slot_files[slot - 1])
    def delete_slot_file(self, slot):
        pth = self.slot_files[slot - 1]
        if os.path.exists(pth): os.remove(pth)
    def delete_all_slots(self):
        for pth in self.slot_files:
            if os.path.exists(pth): os.remove(pth)
    def clear_scores(self):
        if os.path.exists(self.score_file):
            if messagebox.askyesno("Confirm", "Clear leaderboard?"):
                os.remove(self.score_file); messagebox.showinfo("Done", "Leaderboard cleared.")
        else:
            messagebox.showinfo("Info", "Leaderboard already empty.")
