import abc
import pickle
import sys
import pygame
import random
import copy

class BrickRandomizer:
    def __init__(self):
        self.history = ['Z', 'S', 'Z', 'S']
        self.keys = list(Brick.tile_vectors.keys())
    def next_brick(self):
        for roll in range(6):
            brick = random.choice(self.keys)
            if brick not in self.history:
                break
        self.history.pop(0)
        self.history.append(brick)
        return brick


class ClearingManager:
    def __init__(self, state):
        self.score = 0
        self.combo_count = 0
        self.is_hard_dropped = False
        self.state = state
        self.progress_manager = state.progress_manager
    def _move_row_down_by(self, row, offset):
        if offset:
            # print(f"self._move_row_down_by({row}, {offset})")
            for tile in self._tiles_from_row(row):
                # print(f"{tile.position=}")
                tile.position = (tile.position[0], row + offset)
                # print(f"{tile.position=}")

    def clear_lines(self):
        # for i in range(GameState.WORLD_HEIGHT):
        lines_below = 0
        lines_streak = 0
        lines = 0
        for i in range(self.state.WORLD_HEIGHT - 1, -1, -1):
            if self._row_is_full(i):
                lines_below += 1
                lines_streak += 1
                lines += 1
                self._delete_row(i)
            else:
                lines_streak = 0
                self._move_row_down_by(i, lines_below)

        # print(f"{lines=}")

        if lines == 1:
            self.progress_manager.add_score_lines("single")
        elif lines == 2:
            self.progress_manager.add_score_lines("double")
        elif lines == 3:
            self.progress_manager.add_score_lines("triple")
        elif lines == 4:
            self.progress_manager.add_score_lines("tetris")
        else:
            self.progress_manager.end_combo()

        # print(f"{self.progress_manager.score=} {self.progress_manager.level=} {self.progress_manager.lines=}")

    def _row_is_full(self, row):
        for col in range(self.state.WORLD_WIDTH):
            if not self.state.tile_exists((col, row)):
                return False
        # print(f"row {row} is full")
        return True

    def _tiles_from_row(self, row):
        return [tile for tile in self.state.tiles if tile.position[1] == row]

    def _delete_row(self, row):
        self.state.tiles = [tile for tile in self.state.tiles if tile.position[1] != row]

class Tile:
    """Represents one tile of brick"""
    def __init__(self, position, kind, is_brick_tile=False):
        """
        Attributes
        ----------
        position : tuple(int, int)
            Represents position of a tile
        kind :
            Represents kind of brick which  tile belongs/belonged to.
        is_brick_tile : bool
            True for tiles belonging to active brick.
            False for others.
        """
        self.is_brick_tile = is_brick_tile
        self.position = position
        self.kind = kind

    def __str__(self):
        return f"{self.position}: {self.kind}"

    def __eq__(self, other):
        if isinstance(other, Tile):
            return (
                self.is_brick_tile == other.is_brick_tile and
                self.position == other.position and
                self.kind == other.kind
            )
        return False


def tiles_touch_ground(tiles):
    for tile in tiles:
        # print(tile, end=" ")
        if tile.position[1] >= GameState.WORLD_HEIGHT - 1:
            return True
    return False


def tiles_touch_tile(tiles, state_tiles):
    for state_tile in state_tiles:
        for tile in tiles:
            if (
                not state_tile.is_brick_tile and
                tile.position[0] == state_tile.position[0] and
                tile.position[1] == state_tile.position[1] - 1
            ):
                return True
    return False
    # for tile in tiles:
    #     if

class Brick:
    """Represents active brick which player can control"""
    tile_vectors = {
        'O':
        {
            "down": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "left": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "up": ((0, 0), (1, 1), (0, 1), (1, 0)),
            "right": ((0, 0), (1, 1), (0, 1), (1, 0)),

        },
        'I':
        {
            "down": ((-1, 0), (0, 0), (1, 0), (2, 0)),
            "left": ((0, -1), (0, 0), (0, 1), (0, 2)),
            "up": ((-1, 1), (0, 1), (1, 1), (2, 1)),
            "right": ((1, -1), (1, 0), (1, 1), (1, 2)),
        },
        'T':
        {
            "down": ((0, 0), (0, -1), (-1, 0), (1, 0)),
            "left": ((0, 0), (0, -1), (0, 1), (1, 0)),
            "up": ((0, 0), (-1, 0), (1, 0), (0, 1)),
            "right": ((0, 0), (-1, 0), (0, -1), (0, 1))
        },
        'S':
        {
            "down": ((0, 0), (0, -1), (1, -1), (-1, 0)),
            "left": ((0, 0), (0, -1), (1, 0), (1, 1)),
            "up": ((0, 0), (0, 1), (1, 0), (-1, 1)),
            "right": ((0, 0), (-1, 0), (-1, -1), (0, 1))

        },
        'Z':
        {
            "down": ((0, 0), (0, -1), (-1, -1), (1, 0)),
            "left": ((0, 0), (1, 0), (0, 1), (1, -1)),
            "up": ((0, 0), (-1, 0), (0, 1), (1, 1)),
            "right": ((0, 0), (-1, 0), (0, -1), (-1, 1))

        },
        'J':
        {
            "down": ((0, 0), (-1, 0), (1, 0), (-1, -1)),
            "left": ((0, 0), (0, -1), (0, 1), (1, -1)),
            "up": ((0, 0), (-1, 0), (1, 0), (1, 1)),
            "right": ((0, 0), (0, -1), (0, 1), (-1, 1))

        },
        'L':
        {
            "down": ((0, 0), (-1, 0), (1, 0), (1, -1)),
            "left": ((0, 0), (0, -1), (0, 1), (1, 1)),
            "up": ((0, 0), (-1, 0), (1, 0), (-1, 1)),
            "right": ((0, 0), (0, -1), (0, 1), (-1, -1))
        },
    }
    wall_kick_vectors = {
        'I': {
            # (orienation from, orientation to): [test1, ..., test5]
            ("down", "left"): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
            ("left", "down"): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
            ("left", "up"): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
            ("up", "left"): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
            ("up", "right"): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
            ("right", "up"): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
            ("right", "down"): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
            ("down", "right"): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, -1)]
        },
        'other': {
            ("down", "left"): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
            ("left", "down"): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            ("left", "up"): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            ("up", "left"): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
            ("up", "right"): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
            ("right", "up"): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
            ("right", "down"): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
            ("down", "right"): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)]
        }
    }
    spawn_pos = {
        'O': (4, 5),
        'I': (4, 0),
        'T': (4, 3),
        'Z': (4, 3),
        'J': (4, 3),
        'S': (4, 3),
        'L': (4, 3)
    }
    spawn_orientation = {
        'O': "down",
        'I': "down",
        'T': "down",
        'Z': "down",
        'J': "down",
        'S': "down",
        'L': "down"
    }

    def __init__(self, state, position, kind, orientation):
        self.state = state
        self.position = position
        self.kind = kind
        self.orientation = orientation
        self.tiles = []
        self.ghost = GhostBrick(self)
        self.is_moving_left = False
        self.is_moving_right = False
        self.is_soft_dropped = False

    def move(self, position):
        """Moves the brick"""
        return self.move_or_rotate(position, self.orientation)

    def move_or_rotate(self, position, orientation):
        if position == self.position and orientation == self.orientation:
            return False
        for tile in self.tiles:
            for vector in Brick.tile_vectors[self.kind][orientation]:
                if (
                    (x := position[0] + vector[0]) < 0 or
                    x >= GameState.WORLD_WIDTH or
                    (y := position[1] + vector[1]) < 0 or
                    y >= GameState.WORLD_HEIGHT or
                    self.state.tile_exists((x, y))
                ):
                    return False

        self.orientation = orientation
        self.position = position

        while self.tiles:
            self.state.tiles.remove(self.tiles.pop())
        for vector in Brick.tile_vectors[self.kind][orientation]:
            tile = Tile(
                    (position[0] + vector[0], position[1] + vector[1]),
                    self.kind,
                    True
                )
            self.state.tiles.append(tile)
            self.tiles.append(tile)
        self.ghost.update_tiles()
        return True

    def rotate(self, direction):
        new_orientation = self._next_orientation(direction, self.orientation)

        if self.kind == 'I':
            tests = Brick.wall_kick_vectors['I'][(self.orientation, new_orientation)]
        else:
            tests = Brick.wall_kick_vectors['other'][(self.orientation, new_orientation)]

        # print(tests)
        for test in tests:
            if self.move_or_rotate(
                (self.position[0] + test[0], self.position[1] + test[1]),
                new_orientation
            ):
                self._lock_delay_epoch = 1
                return True
            return False

    def _next_orientation(self, direction, old_orientation):
        if direction == "right":
            if old_orientation == "up":
                new_orientation = "right"
            elif old_orientation == "right":
                new_orientation = "down"
            elif old_orientation == "down":
                new_orientation = "left"
            elif old_orientation == "left":
                new_orientation = "up"
        elif direction == "left":
            if old_orientation == "left":
                new_orientation = "down"
            elif old_orientation == "down":
                new_orientation = "right"
            elif old_orientation == "right":
                new_orientation = "up"
            elif old_orientation == "up":
                new_orientation = "left"

        return new_orientation

    def touches_ground(self):
        """Checks whether brick is touching last row of world"""
        return tiles_touch_ground(self.tiles)

    def touches_tile(self):
        """Checks if brick touches any non-brick tile"""
        return tiles_touch_tile(self.tiles, self.state.tiles)

    def lock(self):
        """Ends control of player over the bricks"""
        for brick_tile in self.tiles[:]:
            # print(brick_tile, end=" ")
            idx = self.state.tiles.index(brick_tile)
            self.tiles.remove(brick_tile)
            self.state.tiles[idx].is_brick_tile = False


class GhostBrick():
    def __init__(self, brick):
        self.brick = brick
        self.tiles = []

    def update_tiles(self):
        self.tiles = copy.deepcopy(self.brick.tiles)
        while (
            not tiles_touch_ground(self.tiles) and
            not tiles_touch_tile(self.tiles, self.brick.state.tiles)
        ):
            for tile in self.tiles:
                tile.position = (tile.position[0], tile.position[1] + 1)

MAX_LEVEL = 15

speed = {
        1: 0.01667,
        2: 0.021017,
        3: 0.026977,
        4: 0.035256,
        5: 0.04693,
        6: 0.06361,
        7: 0.0879,
        8: 0.1236,
        9: 0.1775,
        10: 0.2598,
        11: 0.388,
        12: 0.59,
        13: 0.92,
        14: 1.46,
        15: 2.36
    }


class ProgressManager:
   
    def __init__(self, starting_level=1):
        self.level = starting_level
        self.starting_level = starting_level
        self.speed = speed[starting_level]
        self.score = 0
        self.lines = 0
        self.combo_count = 0
        self.is_last_difficult = False
        self.levelup = False
        # self.score_cap

    def add_score_lines(self, action):

        # levelup = False

        if action == "tetris":
            self.score += 800 * self.level * (1.5 if self.is_last_difficult else 1)
            self.lines += 4
            self.is_last_difficult = True
        elif action == "triple":
            self.score += 500 * self.level
            self.lines += 3
            self.is_last_difficult = False
        elif action == "double":
            self.score += 300 * self.level
            self.is_last_difficult = False
            self.lines += 2
        elif action == "single":
            self.score += 100 * self.level
            self.lines += 1
            self.is_last_difficult = False
        elif action == "tspin":
            self.is_last_difficult = True
            pass
        
        if self.starting_level == self.level:
            lines_cap = self.starting_level * 10
        else:
            lines_cap = self.level * 10
        if self.lines >= lines_cap and self.level < MAX_LEVEL:
            self.level += 1
            self.speed = speed[self.level]


        self.combo_count += 1
        if self.combo_count >= 2:
            self.score += 50 * self.level

        # return levelup

    def end_combo(self):
        self.is_last_difficult = False
        self.combo_count = 0
    
    def add_drop_score(self, drop, cells=1):
        if drop == 'hard':
            self.score += 2 * cells
        elif drop == 'soft':
            self.score += 1 * cells

class GameState:
    WORLD_WIDTH = 10
    WORLD_HEIGHT = 30
    VISIBLE_HEIGHT = 20
    PLAYER_SPEED = 5

    def game_lost(self):
        for i in range(GameState.WORLD_WIDTH):
            # print((
            #     i,
            #     GameState.WORLD_HEIGHT - GameState.VISIBLE_HEIGHT - 1
            # ))
            if self.tile_exists((
                i,
                GameState.WORLD_HEIGHT - GameState.VISIBLE_HEIGHT - 1
            )):
                return True
        return False

    def __init__(self):
        self.tiles = []
        self.progress_manager = ProgressManager()
        self.clearing_manager = ClearingManager(self)
        self.brick_randomizer = BrickRandomizer()
        self.highscores = Highscores()
        self.brick = Brick(self, (0, 0), 'O', "down")
        self.ghost = GhostBrick(self.brick)
        self.held_brick_kind = None
        self.held = False
        self.points = 0
        self.level = 1
        self.speed = speed[self.level]

        self.timer = 0
        self._lock_delay_epoch = 1
        self._move_epoch = 1
        # self.is_moving = False

        self.respawn()

    def hold_piece(self):
        if not self.held_brick_kind:
            self.held_brick_kind = self.brick.kind
            self.respawn()
            self.held = True
        elif self.held_brick_kind and not self.held:
            self.held = True
            tmp = self.brick.kind
            self.respawn(self.held_brick_kind)
            self.held_brick_kind = tmp
            
            # self.held_brick_kind = 
            # self.held_brick_kind = BrickRandomizer.next_brick()
    def tile_exists(self, position):
        for tile in self.tiles:
            if tile.position == position and not tile.is_brick_tile:
                return True
        return False

    def move_brick_down(self):

        SOFT_DROP_MULTIPLIER = 10
        self.timer += self.progress_manager.speed * (SOFT_DROP_MULTIPLIER if self.brick.is_soft_dropped else 1)
        if self.timer >= 1:
            self.brick.move(
                (self.brick.position[0], self.brick.position[1] + 1)
            )
            if self.brick.is_soft_dropped:
                self.progress_manager.add_drop_score('soft', 1)
            self._lock_delay_epoch = 1
            self.timer -= 1

    def move_horizontaly(self):
        brick = self.brick
        if brick.is_moving_right and self._move_epoch >= GameState.PLAYER_SPEED:
            brick.move(
                (brick.position[0] + 1, brick.position[1])
            )
            self._move_epoch = 0
            self._lock_delay_epoch = 1

        if brick.is_moving_left and self._move_epoch >= GameState.PLAYER_SPEED:
            brick.move(
                (brick.position[0] - 1, brick.position[1])
            )
            self._move_epoch = 0
            self._lock_delay_epoch = 1
        self._move_epoch += 1

    def hard_drop(self):
        brick = self.brick
        lines = 0
        while not (brick.touches_ground() or brick.touches_tile()):
            brick.move(
                (brick.position[0], brick.position[1] + 1)
            )
            lines += 1
            self._lock_delay_epoch = 30
        self.progress_manager.add_drop_score('hard', lines)

    def respawn(self, held_brick=None):
        if not held_brick:
            brick_kind = self.brick_randomizer.next_brick()
        else:
            brick_kind = held_brick 
        self.brick.kind = brick_kind
        self.brick.move_or_rotate(
            Brick.spawn_pos[brick_kind],
            Brick.spawn_orientation[brick_kind]
        )



    def update(self):
        """Non player controlled after-move actions are here"""

        if (self.brick.touches_ground() or
                self.brick.touches_tile()):
            self._lock_delay_epoch += 1
            self.move_horizontaly()
            if self._lock_delay_epoch >= 30:
                self.brick.lock()
                self._lock_delay_epoch = 1
                self.clearing_manager.clear_lines()
                self.respawn()
                # TODO is it clean? 
                self.held = False
        else:
            self.move_horizontaly()
            self.move_brick_down()
            # check lines


class GameMode(abc.ABC):
    @abc.abstractmethod
    def process_input(self):
        pass

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def draw(self):
        pass
class PlayMode(GameMode):
    def __init__(self, ui):
        self.ui = ui
        self.window = ui.window
        self.game_state = ui.game_state

    def process_input(self):
        events = pygame.event.get()
        brick = self.game_state.brick

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self.reset()
                if event.key == pygame.K_F1 or event.key == pygame.K_ESCAPE:
                    # self.running = not self.running
                    print(len(pickle.dumps(self.game_state, -1)))
                    
                if event.key == pygame.K_LEFT:
                    brick.is_moving_left = True
                if event.key == pygame.K_RIGHT:
                    brick.is_moving_right = True
                if event.key == pygame.K_DOWN:
                    brick.is_soft_dropped = True
                if event.key == pygame.K_x or event.key == pygame.K_UP:
                    brick.rotate("right")
                    pygame.key.set_repeat(0)
                if event.key == pygame.K_RCTRL or event.key == pygame.K_z:
                    brick.rotate("left")
                    pygame.key.set_repeat(0)
                if event.key == pygame.K_SPACE:
                    pygame.key.set_repeat(0)
                    self.game_state.hard_drop()
                if event.key == pygame.K_c:
                    pygame.key.set_repeat(0)
                    self.game_state.hold_piece()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    brick.is_moving_left = False
                if event.key == pygame.K_RIGHT:
                    brick.is_moving_right = False
                if event.key == pygame.K_DOWN:
                    brick.is_soft_dropped = False

    def update(self):
        self.game_state.update()
        progress_manager = self.game_state.progress_manager
        if self.game_state.game_lost():
            self.running = False
            self.ui.show_lost_screen(
                progress_manager.score,
                progress_manager.level,
                progress_manager.lines
            )
            self.game_state.highscores.try_adding("Player", progress_manager.score)
    
    def draw(self):
        """Draws tiles with approperiate colors"""
        color = {
            'O': (255, 255, 0),
            'I': (0, 128, 128),
            'T': (199, 21, 133),
            'Z': (255, 0, 0),
            'S': (0, 255, 0),
            'J': (0, 0, 255),
            'L': (241, 121, 34),
        }

        def draw_tile(self, tile, ghost_tile=False):
            rect = pygame.Rect(
                tile.position[0] * UserInterface.CELL_SIZE,
                tile.position[1] * UserInterface.CELL_SIZE,
                UserInterface.CELL_SIZE,
                UserInterface.CELL_SIZE
            )
            if not ghost_tile:
                pygame.draw.rect(self.window, color[tile.kind], rect)
            else:
                # pygame.draw.rect(self.window, (0, 0, 0), rect)
                pygame.draw.rect(self.window, color[tile.kind], rect, width=2)
                # rect.inflate(-4, -4)
                # pygame.draw.rect(self.window, (255,255,255), rect)

        self.window.fill((255, 255, 255))
        for tile in self.game_state.brick.ghost.tiles:
            draw_tile(self, tile, ghost_tile=True)
        for tile in self.game_state.tiles:
            draw_tile(self, tile)
        # draw line
        line_w = UserInterface.CELL_SIZE * GameState.WORLD_WIDTH
        line_h = UserInterface.CELL_SIZE * (GameState.WORLD_HEIGHT - GameState.VISIBLE_HEIGHT)
        pygame.draw.line(self.window, (0, 0, 255), (0, line_h), (line_w, line_h), 2)
    

class Highscores:
    MAX_SCORES = 5
    PATH = 'scores'
    def __init__(self):
        self.scores = []
        try:
            with open(Highscores.PATH, 'br') as f:
                pass
        except FileNotFoundError:
            self.save()
        self.load()  

    def try_adding(self, name, score):
        if self.is_highscore(score):
            self.scores.append((name, score))
            self.scores.sort(key=lambda x: x[1], reverse=True)
            self.scores = self.scores[:Highscores.MAX_SCORES]
            self.save()


    def is_highscore(self, score):
        return len(self.scores) < Highscores.MAX_SCORES or score > min(self.scores, key=lambda x: x[1])[1]
    
    def save(self):
        with open(Highscores.PATH, 'bw') as f:
            pickle.dump(self.scores, f)
                

    def load(self):
        with open(Highscores.PATH, 'br') as f:
            self.scores = pickle.load(f)
            

class TextButton:
    def __init__(self, font, x, y, text, color, bg_color, hover_color, hover_bg_color):
        self.font = font
        self.text = text
        self.color = color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.hover_bg_color = hover_bg_color
        self.current_color = color
        self.current_bg_color = bg_color
        self.rect = pygame.Rect(x, y, font.size(text)[0], font.size(text)[1])
        self.rect.center = x, y
        self._action = None
        self._clicked = False
    def bind_action(self, action):
        self._action = action

    def update(self, surface):
        text_surf = self.font.render(self.text, True, self.current_color, self.current_bg_color)
        surface.blit(text_surf, self.rect)

    def check_input(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if self._action: 
                self._action()

    def change_color(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.current_color = self.hover_color
            self.current_bg_color = self.hover_bg_color
        else:
            self.current_color = self.color
            self.current_bg_color = self.bg_color


class LostMode(GameMode):
    def __init__(self, ui, font, window, score, level, lines):
        self.window = window
        self.score = score
        self.level = level
        self.lines = lines
        self.ui = ui
        self.score_board = font.render(f"SCORE: {self.score}", True, 'black')
        self.level_board = font.render(f"LEVEL: {self.score}", True, 'black')
        self.lines_board = font.render(f"LEVEL: {self.level}", True, 'black')

        score_rect = self.score_board.get_rect(center=self.window.get_rect().center)
        level_rect = self.score_board.get_rect(center=(125, 350))
        lines_rect = self.score_board.get_rect(center=(125, 450))


        self.window.fill((255, 255, 255))
        self.window.blit(self.score_board, score_rect)
        self.window.blit(self.level_board, level_rect)
        self.window.blit(self.lines_board, lines_rect)
        
        reset_btn = TextButton(font, 125, 100, "RESET", (255,0,255), (0, 255, 0), (243, 213,0), "pink")
        score_btn = TextButton(font, 125, 300, "HIGHSCORE", (255,0,255), (0, 255, 0), (243, 213,0), "pink")
        quit_btn = TextButton(font, 125, 500, "QUIT", (255,0,255), (0, 255, 0), (243, 213,0), "pink")
        self.buttons = [reset_btn, score_btn, quit_btn]
        reset_btn.bind_action(self.ui.reset)
        score_btn.bind_action(self.ui.show_highscore_screen)
        quit_btn.bind_action(self.ui.quit)
 
    def process_input(self):
        events = pygame.event.get()
        for button in self.buttons:
            button.change_color()
            for event in events:
                # TODO nie powinno być pół zarządania eventami tu pół w TextButton
                if event.type == pygame.MOUSEBUTTONDOWN:
                    button.check_input()


    def draw(self):
        for button in self.buttons:
           button.update(self.window)

    def update(self):
        pass
        

class HighscoreMode(GameMode):
    SAVE_PATH = "save"
    def __init__(self, ui):
        self.ui = ui
        self.window = ui.window
        self.game_state = ui.game_state
        self.highscores = ui.game_state.highscores
        self.font = ui.main_font

        reset_btn = TextButton(self.font, 125, 100, "RESET", (255,0,255), (0, 255, 0), (243, 213,0), "pink")
        reset_btn.bind_action(self.ui.reset)
        quit_btn = TextButton(self.font, 125, 500, "QUIT", (255,0,255), (0, 255, 0), (243, 213,0), "pink")
        quit_btn.bind_action(self.ui.quit)
        self.buttons = [reset_btn, quit_btn]
        
        self.window.fill((255, 255, 255))
        y = 200
        for nick, score in self.highscores.scores:
            label = self.font.render(f"{nick}: {score}", True, 'black')
            label_rect = label.get_rect(center=(self.window.get_rect().centerx, y))
            self.window.blit(label, label_rect)
            y += 50
    def process_input(self):
        events = pygame.event.get()
        for button in self.buttons:
            button.change_color()
            for event in events:
                # TODO nie powinno być pół zarządania eventami tu pół w TextButton
                if event.type == pygame.MOUSEBUTTONDOWN:
                    button.check_input()

    def update(self):
        pass

    def draw(self):
        for button in self.buttons:
           button.update(self.window)

class UserInterface:
    """game.Bridges user actions and game state. Uses pyGame"""
    FPS = 60
    CELL_SIZE = 25
    
    def __init__(self):
        
        pygame.init()
        self.main_font = pygame.font.SysFont('liberationserif', 20)
        # Game stateq
        self.game_state = GameState()

        # Window
        WINDOW_WIDTH = self.CELL_SIZE * self.game_state.WORLD_WIDTH
        WINDOW_HEIGHT = self.CELL_SIZE * self.game_state.WORLD_HEIGHT
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.mode = PlayMode(self)

        self.clock = pygame.time.Clock()
        self.running = True

    def reset(self):
        self.game_state = GameState()
        self.clock = pygame.time.Clock()
        self.mode = PlayMode(self)
        self.running = True

    def run(self):
        """Runs the game loop"""
        while True:
            self.mode.process_input()
            if self.running:
                self.mode.update()
                self.mode.draw()
                pygame.display.update()
                self.clock.tick(UserInterface.FPS)

    def show_lost_screen(self, score, level, lines):
        self.mode = LostMode(self, self.main_font, self.window, score, level, lines)

    def show_highscore_screen(self):
        self.mode = HighscoreMode(self)

    def quit(self):
        pygame.quit()
        sys.exit()

    

if __name__ == "__main__":
    pygame.init()
    UserInterface().run()
