import time

import board_utils
from solvers.metrics import SolverResult


class CSPSolver:
    # Constructor and Setup
    def __init__(self, board):
        """Initialize a Sudoku board along with helper structures."""
        self.board = board_utils.parse_board(board)
        self.size, self.box_size = board_utils.board_size(self.board)
        self.rows = [[] for _ in range(self.size)]
        self.cols = [[] for _ in range(self.size)]
        self.boxes = [[] for _ in range(self.size)]
        self.peers = [set() for _ in range(self.size * self.size)]
        self.candidates = [set() for _ in range(self.size * self.size)]
        self.unassigned = set()
        self.assignments = 0
        self.backtracks = 0
        self.recursive_calls = 0

        self.build_houses()
        self.build_peers()
        self.build_candidates()
        self.build_unassigned()

    def build_houses(self):
        """Creates lists of cell indices for each row, column, and box."""
        for cell in range(self.size * self.size):
            row, col, box = self.index_to_coordinates(cell)
            self.rows[row].append(cell)
            self.cols[col].append(cell)
            self.boxes[box].append(cell)

    def build_peers(self):
        """Creates for each cell a set of indices of neighboring cells in the same row, column, or box."""
        for cell in range(self.size * self.size):
            row, col, box = self.index_to_coordinates(cell)
            self.peers[cell] = (
                set(self.rows[row]) | set(self.cols[col]) | set(self.boxes[box])
            ) - {cell}

    def build_candidates(self):
        """Creates a set of possible candidates for each cell if not already assigned."""
        digits = set(range(1, self.size + 1))
        for cell in range(self.size * self.size):
            current_cell_value = self.board[cell]
            if current_cell_value:
                self.candidates[cell] = {current_cell_value}
            else:
                used = set()
                for peer in self.peers[cell]:
                    peer_value = self.board[peer]
                    if peer_value:
                        used.add(peer_value)
                self.candidates[cell] = digits - used

    def build_unassigned(self):
        """Records indices of all currently empty cells (with a value of 0)."""
        for i, cell in enumerate(self.board):
            if cell == 0:
                self.unassigned.add(i)

    # Helper Methods
    def get_board(self) -> str:
        return board_utils.format_board(self.board)

    def index_to_coordinates(self, index):
        row, col = divmod(index, self.size)
        box = (row // self.box_size) * self.box_size + (col // self.box_size)
        return row, col, box

    def is_complete(self) -> bool:
        return len(self.unassigned) == 0

    def validate_board_state(self) -> bool:
        if len(self.board) != self.size * self.size:
            return False

        houses = self.rows + self.cols + self.boxes
        for house in houses:
            seen = [False for _ in range(self.size)]
            for cell in house:
                if self.board[cell] == 0:
                    continue

                if not seen[self.board[cell] - 1]:
                    seen[self.board[cell] - 1] = True
                else:
                    return False

        return True

    # Assignment Methods
    def assign(self, index, value):
        """Assigns a value to a cell and updates the peers' candidate sets."""
        if self.board[index] != 0:
            return set(self.candidates[index]), [], self.board[index] == value

        previous_candidates = set(self.candidates[index])
        if value not in previous_candidates:
            return previous_candidates, [], False

        self.assignments += 1
        self.board[index] = value
        self.candidates[index] = {value}
        self.unassigned.discard(index)

        valid = True
        removed_peers = []
        for peer in self.peers[index]:
            if self.board[peer] == 0 and value in self.candidates[peer]:
                self.candidates[peer].remove(value)
                removed_peers.append(peer)
                if len(self.candidates[peer]) == 0:
                    valid = False

        return previous_candidates, removed_peers, valid

    def unassign(self, index, value, previous_candidates, removed_peers):
        """Removes a cell's value and restores the candidate set."""
        self.board[index] = 0
        self.candidates[index] = previous_candidates
        self.unassigned.add(index)

        for peer in removed_peers:
            self.candidates[peer].add(value)

    # Sudoku Strategies
    def has_empty_candidate_cell(self) -> bool:
        return any(
            self.board[cell] == 0 and len(self.candidates[cell]) == 0
            for cell in self.unassigned
        )

    def eliminate_naked_singles(self) -> tuple[int, bool]:
        "Automatically fills any cells that has exactly only one possible candidate."
        eliminated = 0
        for cell in list(self.unassigned):
            if self.board[cell] != 0:
                continue
            if len(self.candidates[cell]) == 0:
                return eliminated, False
            if len(self.candidates[cell]) == 1:
                _previous, _removed, valid = self.assign(
                    cell, next(iter(self.candidates[cell]))
                )
                if not valid:
                    return eliminated, False
                eliminated += 1
        return eliminated, True

    def eliminate_hidden_singles(self) -> tuple[int, bool]:
        """Fills cells with values that only appear in one place within a row, column, or box."""
        eliminated = 0
        houses = self.rows + self.cols + self.boxes

        for house in houses:
            candidate_locations = [[] for _ in range(self.size + 1)]

            for cell in house:
                if self.board[cell] != 0:
                    continue

                for candidate in self.candidates[cell]:
                    candidate_locations[candidate].append(cell)

            for candidate, cells in enumerate(candidate_locations):
                if candidate == 0 or len(cells) != 1:
                    continue

                cell = cells[0]
                if self.board[cell] != 0:
                    continue

                _previous, _removed, valid = self.assign(cell, candidate)
                if not valid:
                    return eliminated, False
                eliminated += 1
                return eliminated, True

        return eliminated, True

    def find_naked_pairs(self) -> tuple[int, bool]:
        """Finds naked pairs and removes them from the candidates of other cells in the same house."""
        eliminated = 0
        houses = self.rows + self.cols + self.boxes

        for house in houses:
            pairs = {}
            for cell in house:
                if self.board[cell] != 0:
                    continue

                if len(self.candidates[cell]) == 2:
                    pair = frozenset(self.candidates[cell])
                    pairs.setdefault(pair, []).append(cell)

            for pair, pair_cells in pairs.items():
                if len(pair_cells) != 2:
                    continue

                for cell in house:
                    if cell in pair_cells or self.board[cell] != 0:
                        continue

                    before = len(self.candidates[cell])
                    self.candidates[cell] -= pair
                    eliminated += before - len(self.candidates[cell])
                    if len(self.candidates[cell]) == 0:
                        return eliminated, False

        return eliminated, True

    # Heuristics and Search
    def find_mrv(self):
        """Returns the index of an unassigned cell with the fewest remaining candidates."""
        return min(
            self.unassigned, key=lambda index: len(self.candidates[index]), default=None
        )

    def backtrack(self) -> bool:
        """Backtracking with MRV and forward checking."""
        self.recursive_calls += 1

        if self.is_complete():
            return True
        if self.has_empty_candidate_cell():
            return False

        index = self.find_mrv()
        if index is None:
            return True

        for candidate in list(self.candidates[index]):
            previous, removed, valid = self.assign(index, candidate)
            if valid and self.backtrack():
                return True
            self.unassign(index, candidate, previous, removed)
            self.backtracks += 1

        return False

    def solve(self) -> bool:
        """Tries Sudoku strategies before searching for a complete solution."""
        while not self.is_complete():
            if self.has_empty_candidate_cell():
                return False

            eliminated, valid = self.eliminate_naked_singles()
            if not valid:
                return False

            if eliminated == 0:
                eliminated, valid = self.eliminate_hidden_singles()
                if not valid:
                    return False

            if eliminated == 0:
                eliminated, valid = self.find_naked_pairs()
                if not valid:
                    return False

            if eliminated == 0:
                break

        return self.backtrack()


def solve_csp(board: str | list[int]) -> SolverResult:
    start = time.perf_counter()
    solver = None
    solution = None
    status = "error"
    error = None

    try:
        solver = CSPSolver(board)
        if not solver.validate_board_state():
            status = "failed"
            error = "Invalid board state."
        else:
            solved = solver.solve()
            solution = solver.get_board() if solved else None
            status = "solved" if solved else "failed"
    except ValueError as exc:
        status = "failed"
        error = str(exc)
    except Exception as exc:
        error = str(exc)

    solver_metrics = {}
    if solver is not None and status != "error":
        solver_metrics = {
            "backtracks": solver.backtracks,
            "assignments": solver.assignments,
            "recursive_calls": solver.recursive_calls,
        }

    return SolverResult(
        solution=solution,
        status=status,
        runtime_seconds=time.perf_counter() - start,
        error=error,
        **solver_metrics,
    )
