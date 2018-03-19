import random
import copy

class Params:
    FRAUD_REWARD = 1
    FRAUD_FINE = 1
    INITIAL_CELL_VALUE = 10
    DEFAULT_BID = 1

class Cell(object):
    def __init__(self, value=Params.INITIAL_CELL_VALUE, bid=Params.DEFAULT_BID):
        self.value = value
        self.bid = bid

    def suggest_bid(self):
        raise NotImplemented

    def remember_play(self, my_bid, other_bid):
        pass

class AlwaysBid(Cell):
    def suggest_bid(self):
        return self.bid

class AlwaysFraud(Cell):
    def suggest_bid(self):
        return 0

class DeadCell(Cell):
    def __init__(self):
        super().__init__(0)

class TitForTat(Cell):
    def __init__(self):
        self.last_other_bid = 1

    def suggest_bid(self):
        if self.last_other_bid:
            return self.bid
        else:
            return 0

    def remember_play(self, my_bid, other_bid):
        self.last_other_bid = other_bid

def reward_mutual(cell1, cell2, bid1, bid2):
    cell1.value += bid1 + bid2
    cell2.value += bid1 + bid2
    
def reward_one_fraud(cell, other_bid):
    cell.value += other_bid + params.FRAUD_REWARD

def fine_both_fraud(cell1, cell2):
    cell1.value = max(cell1.value - Params.FRAUD_FINE, 0)
    cell2.value = max(cell2.value - Params.FRAUD_FINE, 0)

class Trial(object):
    def __init__(self, reward_mutual=reward_mutual, reward_one_fraud=reward_one_fraud, fine_both_fraud=fine_both_fraud):
        self.reward_mutual = reward_mutual
        self.reward_one_fraud = reward_one_fraud
        self.fine_both_fraud = fine_both_fraud

    def play(self, cell1, cell2):
        if isinstance(cell1, DeadCell) or isinstance(cell2, DeadCell) or cell1 == cell2:
            return
        bid1 = self.bid_cell(cell1)
        bid2 = self.bid_cell(cell2)
        if bid1 * bid2 == 0:
            if bid1 == 0 and bid2 == 0:
                self.fine_both_fraud(cell1, cell2)
            elif bid1 == 0:
                self.reward_one_fraud(cell1, bid2)
            else:
                self.reward_one_fraud(cell2, bid1)
        else:
            self.reward_mutual(cell1, cell2, bid1, bid2)

        cell1.remember_play(bid1, bid2)
        cell2.remember_play(bid2, bid1)

    def bid_cell(self, cell):
        bid = cell.suggest_bid()
        if cell.value - bid >= 0:
            cell.value -= bid
            return bid
        return 0

class Grid(object):
    """Rectangular grid, wrapped on borders by default with 8 neighbours."""

    def __init__(self, height, width, fill, border=False):
        self.height = height
        self.width = width
        if border:
            self.height += 2
            self.width += 2
        self.grid = list()
        if isinstance(fill, Cell):
            self.grid = [copy.deepcopy(fill) for x in range(self.height * self.width)]
        else:
            raise NotImplementedError('Unsupported fill type: {}.'.format(type(fill)))
        if border:
            for i in range(self.height):
                self.grid[i * self.width] = DeadCell()
                self.grid[(i + 1) * self.width - 1] = DeadCell()
            for i in range(1, self.width - 1):
                self.grid[i] = DeadCell()
                self.grid[self.height * self.width - 1 - i] = DeadCell()

    def get(self, row, col):
        return self.grid[(row % self.height) * self.width + (col % self.width)]

    def set(self, row, col, cell):
        self.grid[(row % self.height) * self.width + (col % self.width)] = cell

    def get_neighbours(self, row, col):
        neighbours = list()
        for r in (-1, 0, 1):
            for c in (-1, 0, 1):
                if r == 0 and c == 0:
                    continue
                neighbours.append(self.get(row + r, col + c))
        return neighbours

    def traverse_grid(self, f):
        for r in range(self.height):
            for c in range(self.width):
                f(self.get(r, c), r, c)

    def __str__(self):
        res = 'Grid object:\n[\n'
        for i in range(self.height):
            res += ' '
            res += '\t'.join([str(x.value) for x in self.grid[i * self.width: (i + 1) * self.width]]) + '\n'
        res += ']\n'
        return res

    def __repr__(self):
        return self.__str__()

def get_grid_from_file(file_name):
    with open(file_name) as grid_file:
        lines = grid_file.readlines()
        for i, line in enumerate(lines):
            lines[i] = [int(x) for x in line.split()]
        height = len(lines)
        width = len(lines[0])
        grid = Grid(height, width, DeadCell())
        for line, row in zip(lines, range(height)):
            for t, col in zip(line, range(width)):
                cell = DeadCell()
                if t == 1:
                    cell = AlwaysBid()
                elif t == 2:
                    cell = AlwaysFraud()
                elif t == 3:
                    cell = TitForTat()
                grid.set(row, col, cell)
    return grid

def play(grid, trial, num_rounds, result_getter):
    def play_with_neighbours(cell, row, col):
        neighbours = grid.get_neighbours(row, col)
        random.shuffle(neighbours)
        for n in neighbours:
            trial.play(cell, n)

    for round_i in range(num_rounds):
        grid.traverse_grid(play_with_neighbours)
    return result_getter(grid)

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Cellular automata based on two prisoners problem.')
    parser.add_argument('goal', type=str, action='store',
                        help='Goal as a function with one parameter - grid')
    parser.add_argument('num_rounds', type=int, action='store',
                        help='Cellular automata width')

    subparsers = parser.add_subparsers(help='help for subcommand')
    grid_file_parser = subparsers.add_parser('grid_file', help='Use file to construct grid')
    grid_file_parser.add_argument('grid_file', type=str, action='store',
                                  help='File with grid layout')

    #parser.add_argument('height', type=int, action='store',
    #                    help='Cellular automata height')
    #parser.add_argument('width', type=int, action='store',
    #                    help='Cellular automata width')

    args = parser.parse_args()
    trial = Trial()
    if args.grid_file:
        grid = get_grid_from_file(args.grid_file)
    else:
        grid = Grid(args.height, args.width, AlwaysFraud(), True)
    goal_row, goal_col = [int(x) for x in args.goal.split()]
    result = play(grid, trial, args.num_rounds, lambda grid: grid.get(goal_row, goal_col).value)
    print(result)
