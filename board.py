import random
from collections import deque
class Board:
    #Represents the Minesweeper board, which stores grid state, mine position, revealed and flagged cell, handles mines placement, computes numbers around mines, perform flood fill reveal for zero tiles, compute e3BV metric
    def __init__(self, rows, cols, mines, seed=None, grid=None, revealed=None, flagged=None):
        self.rows = rows; self.cols = cols; self.mines = mines; self.seed = seed
        #Optional pre loaded board
        self.grid = grid; self.revealed = revealed
        #player placed flags
        self.flagged = set(flagged) if flagged else set()
        #Actual mines positions
        self.mine_set = set()
        #If grid not provided, initialize empty
        if self.grid is None or self.revealed is None: self._init_empty()
        #Indicate if mines have been placed
        self.placed = False
    def _init_empty(self):
        #Initialize an empty board with no mines  and all cells unrevealed
        self.grid = [["0" for _ in range(self.cols)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
    def place_mines(self, fixed_seed=None):
        #Place mines randomly on the board, if fixed_seed is provided, use that seed
        if fixed_seed is not None:
            self.seed = int(fixed_seed); random.seed(self.seed)
        elif self.seed is not None:
            random.seed(int(self.seed))
        else:
            self.seed = random.randint(0, 10**9); random.seed(self.seed)
        #Reset board state
        self._init_empty(); self.flagged = set()
        tot = self.rows * self.cols
        #Choose unique positions for mines
        pos = random.sample(range(tot), self.mines)
        self.mine_set = set()
        for idx in pos:
            r, c = divmod(idx, self.cols)
            self.mine_set.add((r, c)); self.grid[r][c] = "M"
        #Compute numbers around mines
        self._compute_numbers()
        #Ensure correct number of mines placed
        if len(self.mine_set) != self.mines:
            rem = [p for p in range(tot) if (p // self.cols, p % self.cols) not in self.mine_set]
            while len(self.mine_set) < self.mines and rem:
                p = random.choice(rem); rem.remove(p)
                rr, cc = divmod(p, self.cols)
                self.mine_set.add((rr, cc)); self.grid[rr][cc] = "M"
            self._compute_numbers()
        return self.seed
    def place_mines_avoiding(self, avoid_cell):
        #Place mines while ensuring the first click never contain a mine
        if self.seed is not None:
            random.seed(int(self.seed))
        else:
            self.seed = random.randint(0, 10**9); random.seed(self.seed)
        self._init_empty(); self.flagged = set()
        ar, ac = avoid_cell
        #compute all protected cell
        bnd = set()
        for i in range(-1, 2):
            for j in range(-1, 2):
                nr, nc = ar + i, ac + j
                if 0 <= nr < self.rows and 0 <= nc < self.cols: bnd.add(nr * self.cols + nc)
        tot = self.rows * self.cols
        #Fallback if not enough free space
        alw = [p for p in range(tot) if p not in bnd]
        #choose mine positions
        if len(alw) < self.mines: alw = [p for p in range(tot) if p != (ar * self.cols + ac)]
        pos = set()
        if len(alw) >= self.mines:
            pos = set(random.sample(alw, self.mines))
        else:
            cnd = [p for p in range(tot) if p != (ar * self.cols + ac)]
            while len(pos) < self.mines and cnd:
                p = random.choice(cnd); cnd.remove(p); pos.add(p)
        self.mine_set = set()
        #assign mines
        for idx in pos:
            r, c = divmod(idx, self.cols)
            self.mine_set.add((r, c)); self.grid[r][c] = "M"
        #guarantee avoid_cell is safe
        if (ar, ac) in self.mine_set:
            self.mine_set.remove((ar, ac)); self.grid[ar][ac] = "0"
            #Pick a new mine somewhere else
            tps = set(range(self.rows * self.cols))
            cur = {p[0] * self.cols + p[1] for p in self.mine_set}
            rem = list(tps - cur - {ar * self.cols + ac})
            if rem:
                pk = random.choice(rem); rr, cc = divmod(pk, self.cols)
                self.mine_set.add((rr, cc)); self.grid[rr][cc] = "M"
        #Recalculate numbers 
        self._compute_numbers()
        #Fix mismatched mines count if needed 
        if len(self.mine_set) != self.mines:
            tps = [(p // self.cols, p % self.cols) for p in range(self.rows * self.cols)]
            for rr, cc in tps:
                if len(self.mine_set) >= self.mines: break
                if (rr, cc) not in self.mine_set and not (rr == ar and cc == ac):
                    self.mine_set.add((rr, cc)); self.grid[rr][cc] = "M"
            #Removed extra if necessary 
            while len(self.mine_set) > self.mines:
                rem = next(iter(self.mine_set))
                if rem == (ar, ac): break
                self.mine_set.remove(rem); self.grid[rem[0]][rem[1]] = "0"
            self._compute_numbers()
        return self.seed
    def _compute_numbers(self):
        #Fill grid with numbers representing mines adjacent to each cell
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mine_set:
                    self.grid[r][c] = "M"; continue
                cnt = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0: continue
                        nr, nc = r + i, c + j
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) in self.mine_set: cnt += 1
                self.grid[r][c] = str(cnt)
    def reveal(self, r, c):
        #Reveal a cell, if its a zero, perform flood fill revealing connected zero region, returns a list of revealed cell
        if self.revealed[r][c] or (r, c) in self.flagged: return []
        rcs = []
        #zero tile -> multi tiled flood reveal 
        if self.grid[r][c] == "0":
            stk = [(r, c)]
            while stk:
                cr, cc = stk.pop()
                if self.revealed[cr][cc]: continue
                self.revealed[cr][cc] = True
                rcs.append((cr, cc, self.grid[cr][cc]))
                if self.grid[cr][cc] == "0":
                    #Add neighbors to stack 
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            nr, nc = cr + i, cc + j
                            if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.revealed[nr][nc]: stk.append((nr, nc))
        #Number tile -> reveal only this tile
        else:
            self.revealed[r][c] = True; rcs.append((r, c, self.grid[r][c]))
        return rcs
    def toggle_flag(self, r, c):
        #Flag or unflag a cell, returns True  when flagged, False when unflagged, None if invalid
        if self.revealed[r][c]: return None
        if (r, c) in self.flagged:
            self.flagged.remove((r, c)); return False
        self.flagged.add((r, c)); return True
    def check_win(self):
        #A win happens when all non mine cells are revealed
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in self.mine_set and not self.revealed[r][c]: return False
        return True
    def reveal_all_mines(self):
        #Return a list of all mine positions for display after losing  
        return [(r, c, "M") for (r, c) in self.mine_set]
    def _reveal_simulation(self, start):
        #Simulate flood fill without modifying the real board, used in computing e3BV
        sr, sc = start; seen = set()
        #if not a zero, only this cell would reveal 
        if (sr, sc) in self.mine_set: return seen
        if self.grid[sr][sc] != "0":
            seen.add((sr, sc)); return seen
        #BFS flood fill 
        q = deque(); q.append((sr, sc)); seen.add((sr, sc))
        while q:
            r, c = q.popleft()
            if self.grid[r][c] == "0":
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nr, nc = r + i, c + j
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in seen:
                            seen.add((nr, nc))
                            if self.grid[nr][nc] == "0": q.append((nr, nc))
        return seen
    def compute_e3bv(self, first_click=None):
        #Compute the e3BV metric (estimated number of optimal logical clicks), used to rate board difficulty or solver efficiency
        #Reveal region caused by the first click
        rbf = set()
        if first_click is not None:
            fr, fc = first_click
            if 0 <= fr < self.rows and 0 <= fc < self.cols: rbf = self._reveal_simulation(first_click)
        #Count zero regions not part of the first click reveal 
        vst = set(); zrg = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == "0" and (r, c) not in vst and (r, c) not in rbf:
                    zrg += 1; q = deque(); q.append((r, c)); vst.add((r, c))
                    #flood through zero cluster 
                    while q:
                        cr, cc = q.popleft()
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                nr, nc = cr + i, cc + j
                                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in vst and (nr, nc) not in rbf:
                                    if self.grid[nr][nc] == "0":
                                        vst.add((nr, nc)); q.append((nr, nc))
        #All remaining zero cells not revealed from first click 
        zcs = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == "0" and (r, c) not in rbf: zcs.add((r, c))
        #Count isolated number squares
        iso = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mine_set: continue
                if (r, c) in rbf: continue
                if self.grid[r][c] == "0": continue
                #Check if it borders any zero region 
                atz = False
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nr, nc = r + i, c + j
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if (nr, nc) in rbf or (nr, nc) in zcs:
                                atz = True; break
                    if atz: break
                if not atz: iso += 1
        e3bv = zrg + iso
        return e3bv
