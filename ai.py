import itertools
from collections import defaultdict
from abc import ABC, abstractmethod

def restore_path(start, goal, parent_dict):
    try:
        path = []
        curr = goal
        while parent_dict[curr] != start:
            path.append(curr)
            curr = parent_dict[curr]
        path.append(curr)
        path.reverse()
        return path
    except:
        print(start, goal, parent_dict)
        return [start]


class PathFinder(ABC):
    @abstractmethod
    def find_pred(self, start, is_goal, get_neighbors):
        pass

    def find_path(self, start, goal, get_neighbors):
        return self.find_pred(start, lambda p: p == goal, get_neighbors)

    def eval(self, path):
        return len(path)

#depth-first-search
class DFS(PathFinder):
    def find_pred(self, start, is_goal, get_neighbors):
        stack = []
        curr = start
        parents = {}
        visited = set()
        stack.append(start)
        steps = 0
        while not is_goal(curr) and len(stack) > 0:
            steps += 1
            curr = stack.pop()
            visited.add(curr)
            derivatives = get_neighbors(curr)
            for derivative in derivatives:
                if not derivative in visited and not derivative in stack:
                    parents[derivative] = curr
                    stack.append(derivative)
        if is_goal(curr):
            return restore_path(start, curr, parents), steps

# пошук у ширину
class BFS(PathFinder):
    def find_pred(self, start, is_goal, get_neighbors):
        queue = []
        curr = start
        parents = {}
        visited = set()
        queue.insert(0, start)
        steps = 0
        while not is_goal(curr) and len(queue) > 0:
            steps += 1
            curr = queue.pop()
            visited.add(curr)
            derivatives = get_neighbors(curr)
            for derivative in derivatives:
                if not derivative in visited and not derivative in queue:
                    parents[derivative] = curr
                    queue.insert(0, derivative)
        if is_goal(curr):
            return restore_path(start, curr, parents), steps


# Iterative deepening depth-first search
class IDFS(PathFinder):
    def find_pred(self, start, is_goal, get_neighbors):
        dParents.clear()
        steps = 0
        for depth in itertools.count():
            found, remaining, stepc = DLS(start, is_goal, depth, get_neighbors)
            steps += stepc
            dVisited.clear()
            if found:
                return restore_path(start, found, dParents), steps
            elif not remaining:
                return None, steps

dParents = dict()
dVisited = set()

# depth limited search
def DLS(node, is_goal, depth, get_neighbors):
    if node in dVisited: return None, False, 1
    dVisited.add(node)
    if depth == 0:
        if is_goal(node):
            return node, None, 1
        else:
            return None, True, 1
    any_remaining = False
    for child in get_neighbors(node):
        if child not in dVisited:
            dParents[child] = node
        found, remaining, steps = DLS(child, is_goal, depth - 1, get_neighbors)
        if found:
            return found, True, steps + 1
        if remaining:
            any_remaining = True
    return None, any_remaining, steps + 1


class Greedy(PathFinder):
    def find_pred(self, start, is_goal, get_neighbors):
        goal = BFS().find_pred(start, is_goal, get_neighbors)[0][-1]
        return self.find_path(start, goal, get_neighbors)

    def find_path(self, start, goal, get_neighbors, heuristic=lambda a, b:sum(abs(x - y) for x, y in zip(a,b))):
        openset = set()
        closedset = set()
        current = start
        openset.add(current)
        parents = {}
        h = defaultdict(int)
        steps = 0
        while len(openset) > 0:
            steps += 1
            current = min(openset, key=lambda o: h[o])
            if current == goal:
                return restore_path(start, current, parents), steps
            openset.remove(current)
            closedset.add(current)
            for node in get_neighbors(current):
                if node in closedset:
                    continue
                if node in openset:
                    continue
                h[node] = heuristic(node, goal)
                parents[node] = current
                openset.add(node)

    def find_pred2(self, start, is_goal, get_neighbors, heuristic):
        openset = set()
        closedset = set()
        current = start
        openset.add(current)
        parents = {}
        h = defaultdict(int)
        steps = 0
        while len(openset) > 0:
            steps += 1
            current = min(openset, key=lambda o: h[o])
            if is_goal(current):
                return restore_path(start, current, parents), steps
            openset.remove(current)
            closedset.add(current)
            for node in get_neighbors(current):
                if node in closedset:
                    continue
                if node in openset:
                    continue
                h[node] = heuristic(node)
                parents[node] = current
                openset.add(node)

if __name__ == '__main__':
    def get_neighbors(X):
        ret = []
        for neighbor in [
            (X[0], X[1] + 1),
            (X[0] + 1, X[1]),
            (X[0], X[1] - 1),
            (X[0] - 1, X[1]),
        ]:
            if neighbor[0] >= 0 and neighbor[0] < 10 and neighbor[
                    1] > 0 and neighbor[1] < 10:
                ret.append(neighbor)
        return ret
    methods = [BFS(), DFS(), IDFS()]
    for method in methods:
        print(method, method.find_path((0, 3), (5, 8), get_neighbors))
