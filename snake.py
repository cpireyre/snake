import curses
from curses import wrapper
from itertools import count, islice

from collections import deque
import random
from random import randint
random.seed(1)


def orientation(u, v):
    uy, ux, vy, vx = u, v
    return ((uy - vy) // abs(uy - vy), (ux - vx) // abs(ux - vx))
orientations = {(1, 0): ">",
        (-1, 0): "<",
        (0, 1): "^",
        (0, -1): "v",}
def pos(key, y, x, H, W):
    if key == curses.KEY_LEFT:
        x = (x - 1) % (W - 1)
    elif key == curses.KEY_RIGHT:
        x = (x + 1) % (W - 1)
    elif key == curses.KEY_DOWN:
        y = (y + 1) % (H - 1)
    elif key == curses.KEY_UP:
        y = (y - 1) % (H - 1)
    return (y, x)


def shortestPath(source, sink, H, W, S):
    Q = deque([(source, [])])
    seen = set(S)

    def neighbors(y, x):
        return {                (y, (x + 1) % W), (y, (x - 1) % W),
                ((y + 1) % H, x), ((y - 1) % H, x),
                }
    while Q:
        v, path = Q.popleft()
        if v == sink:
            return path
        moves = neighbors(*v) - seen
        Q.extend((move, path + [v]) for move in moves)
        seen.update(moves)

    return None
        
def main(stdscr):
    stdscr.clear()
    curses.curs_set(0)
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    stdscr.timeout(40)

    H, W = stdscr.getmaxyx()
    y, x = H // 2, W // 2

    def draw(stdscr, game, H, W):
        snake, snakeSize, apples, apple, path = game
        stdscr.clear()
        stdscr.addstr(0, W // 3, "BADGER'S SNAKE. Score: %d" % (snakeSize - 1,))
        stdscr.addstr(*apple, "@", curses.A_BOLD | curses.color_pair(203))
        if path:
            for y, x in path:
                stdscr.addstr(y % H, x % W, ".")
        for y, x in snake:
            if (y, x) != snake[-1]:
                stdscr.addstr(y, x, "&", curses.color_pair(29))
            else:
                stdscr.addstr(y, x, "&", curses.A_BOLD | curses.color_pair(29))
        stdscr.refresh()

    input = (stdscr.getch() for _ in count())
    snake = deque([(y, x)])
    snakeSize = 1
    apples = ((randint(2, H - 2), randint(2, W - 2)) for _ in range(100))
    apple = next(apples)
    path = shortestPath((y, x), apple, H - 1, W - 1, snake)
    game = (snake, snakeSize, apples, apple, path)

    def move(key, snake, snakeSize, apples, apple, path):
        if key != -1:
            coord = pos(key, *snake[-1], H, W)
        else:
            coord = path[1]
        if snakeSize > 1 and coord == snake[-2]:
            deltay = snake[-1][0] - coord[0]
            deltax = snake[-1][1] - coord[1]
            coord = ((snake[-1][0] + deltay) % H, (snake[-1][1] + deltax) % W)
        if coord not in snake:
            if coord == apple:
                apple = next(apples, 0)
                snakeSize += 1
                if not apple:
                    return snakeSize - 1
            elif len(snake) >= snakeSize:
                snake.popleft()
            snake.append(coord)
            path = shortestPath(coord, apple, H-1, W-1, snake)
            return (snake, snakeSize, apples, apple, path)
        else:
            return snakeSize - 1

    lastkey = None
    draw(stdscr, game, H, W)
    for key in input:
        if key == -1 and lastkey == None:
            continue
        if key == -1:
            key = lastkey
        else:
            lastkey = key
        game = move(key, *game)
        if type(game) == tuple:
            draw(stdscr, game, H, W)
        else:
            curses.flash()
            stdscr.addstr(H // 2, W // 2, "You win! Score: %d" % (game,))
            stdscr.refresh()
            curses.delay_output(3000)
            return game
score = wrapper(main)

def seecolors(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    stdscr.addstr(0, 0, '{0} colors available'.format(curses.COLORS))
    maxy, maxx = stdscr.getmaxyx()
    maxx = maxx - maxx % 5
    x = 0
    y = 1
    try:
        for i in range(0, curses.COLORS):
            stdscr.addstr(y, x, '{0:5}'.format(i), curses.color_pair(i))
            x = (x + 5) % maxx
            if x == 0:
                y += 1
    except curses.ERR:
        pass
    stdscr.getch()
# wrapper(seecolors)
