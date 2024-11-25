import pygame
import threading
import time
import random
from queue import Queue
from dataclasses import dataclass
from typing import List, Tuple
import math
import sys

@dataclass
class Position:
    x: int
    y: int

    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        
    def collides_with(self, other: 'Position') -> bool:
        return math.fabs(self.x - other.x) < 0.8 and math.fabs(self.y - other.y) < 0.8

class SharedState:
    def __init__(self):
        self.lock = threading.Lock()
        self.score = 0
        self.running = True
        self.power_up_active = False
        self.power_up_timer = 0
        self.move_queue = Queue()
        self.game_over = False
        self.win = False
        self.debug = True

class Ghost(threading.Thread):
    def __init__(self, game, ghost_id: int, start_pos: Position, personality: str):
        super().__init__()
        self.game = game
        self.ghost_id = ghost_id
        self.position = start_pos
        self.start_pos = start_pos
        self.personality = personality
        self.is_blue = False
        self.daemon = True
        self.is_eaten = False
        self.base_speed = 0.2
        self.last_position = None

    def calculate_move(self) -> Tuple[int, int]:
        with self.game.shared_state.lock:
            if self.is_eaten:
                dx = self.start_pos.x - self.position.x
                dy = self.start_pos.y - self.position.y
                if abs(dx) < 0.1 and abs(dy) < 0.1:
                    self.is_eaten = False
                    self.is_blue = False
                    return (0, 0)
                else:
                    return (1 if dx > 0 else -1 if dx < 0 else 0,
                           1 if dy > 0 else -1 if dy < 0 else 0)

            player_x = self.game.player_pos.x
            player_y = self.game.player_pos.y
            
            moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            valid_moves = []
            
            for dx, dy in moves:
                new_x = self.position.x + dx
                new_y = self.position.y + dy
                if self.game.is_valid_move(Position(new_x, new_y)):
                    if (self.last_position is None or 
                        not (abs(new_x - self.last_position.x) < 0.1 and 
                             abs(new_y - self.last_position.y) < 0.1)):
                        valid_moves.append((dx, dy))
            
            if not valid_moves:
                if self.last_position:
                    for dx, dy in moves:
                        new_x = self.position.x + dx
                        new_y = self.position.y + dy
                        if self.game.is_valid_move(Position(new_x, new_y)):
                            valid_moves.append((dx, dy))
                if not valid_moves:
                    return (0, 0)
            
            if self.is_blue:
                distances = []
                for dx, dy in valid_moves:
                    new_x = self.position.x + dx
                    new_y = self.position.y + dy
                    dist = abs(new_x - player_x) + abs(new_y - player_y)
                    distances.append((dist, (dx, dy)))
                return max(distances, key=lambda x: x[0])[1]
            
            if self.personality == "chase":
                distances = []
                for dx, dy in valid_moves:
                    new_x = self.position.x + dx
                    new_y = self.position.y + dy
                    dist = abs(new_x - player_x) + abs(new_y - player_y)
                    distances.append((dist, (dx, dy)))
                return min(distances, key=lambda x: x[0])[1]
            else:
                if random.random() < 0.3:
                    distances = []
                    for dx, dy in valid_moves:
                        new_x = self.position.x + dx
                        new_y = self.position.y + dy
                        dist = abs(new_x - player_x) + abs(new_y - player_y)
                        distances.append((dist, (dx, dy)))
                    return min(distances, key=lambda x: x[0])[1]
                return random.choice(valid_moves)

    def handle_collision(self) -> None:
        with self.game.shared_state.lock:
            if self.position.collides_with(self.game.player_pos):
                if self.is_blue and not self.is_eaten:
                    if self.game.shared_state.debug:
                        print(f"Ghost {self.ghost_id} eaten!")
                    self.is_eaten = True
                    self.game.shared_state.score += 200
                elif not self.is_blue and not self.is_eaten:
                    if self.game.shared_state.debug:
                        print(f"Player caught by ghost {self.ghost_id}!")
                    self.game.shared_state.game_over = True

    def run(self):
        while self.game.shared_state.running:
            if self.game.shared_state.game_over or self.game.shared_state.win:
                break
            
            self.last_position = Position(self.position.x, self.position.y)
            
            dx, dy = self.calculate_move()
            with self.game.shared_state.lock:
                new_pos = Position(self.position.x + dx, self.position.y + dy)
                if self.game.is_valid_move(new_pos):
                    self.position = new_pos
            
            self.handle_collision()
            
            speed = self.base_speed
            if self.is_blue:
                speed *= 1.5
            if self.is_eaten:
                speed *= 0.5
            time.sleep(speed)

class Game:
    def __init__(self):
        self.CELL_SIZE = 20
        self.BOARD_WIDTH = 28
        self.BOARD_HEIGHT = 31
        self.SCREEN_WIDTH = self.BOARD_WIDTH * self.CELL_SIZE
        self.SCREEN_HEIGHT = self.BOARD_HEIGHT * self.CELL_SIZE + 50

        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man")
        self.clock = pygame.time.Clock()

        self.shared_state = SharedState()
        self.player_pos = Position(x=12, y=23)
        self.player_direction = "right"
        self.player_thread = threading.Thread(target=self.handle_player_input)
        self.ghosts = []
        self.board = self.create_board()
        ghost_info = [
            (Position(14, 12), "chase"),
            (Position(14, 15), "random")
        ]
        for i, (pos, personality) in enumerate(ghost_info):
            ghost = Ghost(self, i, pos, personality)
            self.ghosts.append(ghost)

    def create_board(self) -> List[List[str]]:
        layout = [
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
            "W............WW............W",
            "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
            "WeWWWW.WWWWW.WW.WWWWW.WWWWeW",
            "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
            "W..........................W",
            "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
            "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
            "W......WW....WW....WW......W",
            "WWWWWW.WWWWW WW WWWWW.WWWWWW",
            "WWWWWW.WWWWW WW WWWWW.WWWWWW",
            "WWWWWW.WW          WW.WWWWWW",
            "WWWWWW.WW WWW  WWW WW.WWWWWW",
            "WWWWWW.WW W      W WW.WWWWWW",
            "          W      W          ",
            "WWWWWW.WW W      W WW.WWWWWW",
            "WWWWWW.WW WWWWWWWW WW.WWWWWW",
            "WWWWWW.WW          WW.WWWWWW",
            "WWWWWW.WW WWWWWWWW WW.WWWWWW",
            "WWWWWW.WW WWWWWWWW WW.WWWWWW",
            "W............WW............W",
            "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
            "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
            "We..WW................WW..eW",
            "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
            "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
            "W......WW....WW....WW......W",
            "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
            "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
            "W..........................W",
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWW"
        ]
        return [[cell for cell in row] for row in layout]

    def is_valid_move(self, pos: Position) -> bool:
        if 0 <= pos.x < self.BOARD_WIDTH and 0 <= pos.y < self.BOARD_HEIGHT:
            return self.board[pos.y][pos.x] != 'W'
        return False
    
    def handle_player_input(self):
        while self.shared_state.running and not self.shared_state.game_over:
            with self.shared_state.lock:
                if not self.shared_state.move_queue.empty():
                    direction = self.shared_state.move_queue.get()
                    
                    dx, dy = 0, 0
                    if direction == "left": dx = -1
                    elif direction == "right": dx = 1
                    elif direction == "up": dy = -1
                    elif direction == "down": dy = 1

                    new_pos = Position(self.player_pos.x + dx, self.player_pos.y + dy)

                    if self.is_valid_move(new_pos):
                        self.player_pos = new_pos
                        cell = self.board[new_pos.y][new_pos.x]
                        if cell == '.':
                            self.shared_state.score += 10
                            self.board[new_pos.y][new_pos.x] = ' '
                        elif cell == 'e':
                            if self.shared_state.debug:
                                print("Power pellet eaten!")
                            self.shared_state.score += 50
                            self.board[new_pos.y][new_pos.x] = ' '
                            self.shared_state.power_up_active = True
                            self.shared_state.power_up_timer = 150
                            for ghost in self.ghosts:
                                if not ghost.is_eaten:
                                    ghost.is_blue = True

            time.sleep(0.1)  # Prevent CPU hogging

    def render_frame(self):
        self.screen.fill((0, 0, 0))

        # Draw board
        for y in range(self.BOARD_HEIGHT):
            for x in range(self.BOARD_WIDTH):
                cell = self.board[y][x]
                rect = pygame.Rect(x * self.CELL_SIZE, y * self.CELL_SIZE, 
                                 self.CELL_SIZE, self.CELL_SIZE)
                if cell == 'W':
                    pygame.draw.rect(self.screen, (0, 0, 255), rect)
                elif cell == '.':
                    pygame.draw.circle(self.screen, (255, 255, 255), rect.center, 4)
                elif cell == 'e':
                    pygame.draw.circle(self.screen, (255, 0, 255), rect.center, 8)

        # Draw player
        pygame.draw.circle(self.screen, (255, 255, 0),
                         (self.player_pos.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                          self.player_pos.y * self.CELL_SIZE + self.CELL_SIZE // 2),
                         self.CELL_SIZE // 2 - 2)

        # Draw ghosts
        for ghost in self.ghosts:
            color = (100, 100, 100) if ghost.is_eaten else (
                (0, 0, 255) if ghost.is_blue else (
                    (255, 0, 0) if ghost.personality == "chase" else (255, 182, 85)
                ))
            pygame.draw.circle(self.screen, color,
                             (ghost.position.x * self.CELL_SIZE + self.CELL_SIZE // 2,
                              ghost.position.y * self.CELL_SIZE + self.CELL_SIZE // 2),
                             self.CELL_SIZE // 2 - 4)

        # Draw UI
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.shared_state.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, self.SCREEN_HEIGHT - 40))

        if self.shared_state.power_up_active:
            power_text = font.render(f"Power: {self.shared_state.power_up_timer//30}", True, (255, 255, 0))
            self.screen.blit(power_text, (200, self.SCREEN_HEIGHT - 40))

        if self.shared_state.game_over:
            game_over_text = font.render("Game Over", True, (255, 0, 0))
            self.screen.blit(game_over_text, (self.SCREEN_WIDTH // 2 - 60, self.SCREEN_HEIGHT // 2))
        elif self.shared_state.win:
            win_text = font.render("You Win!", True, (0, 255, 0))
            self.screen.blit(win_text, (self.SCREEN_WIDTH // 2 - 50, self.SCREEN_HEIGHT // 2))

        pygame.display.flip()

    def cleanup(self):
        self.shared_state.running = False
        pygame.quit()
        
        # Join player thread with timeout
        if self.player_thread.is_alive():
            self.player_thread.join(timeout=1.0)
            
        # Join ghost threads with timeout
        for ghost in self.ghosts:
            if ghost.is_alive():
                ghost.join(timeout=1.0)

    def start(self):
        # Start ghost threads
        for ghost in self.ghosts:
            ghost.start()
        self.player_thread.start()
        
        try:
            while self.shared_state.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.shared_state.running = False
                        self.cleanup()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            self.shared_state.move_queue.put("left")
                        elif event.key == pygame.K_RIGHT:
                            self.shared_state.move_queue.put("right")
                        elif event.key == pygame.K_UP:
                            self.shared_state.move_queue.put("up")
                        elif event.key == pygame.K_DOWN:
                            self.shared_state.move_queue.put("down")
                        elif event.key == pygame.K_ESCAPE:
                            self.shared_state.running = False
                            self.cleanup()
                            return

                # Update power-up timer
                if self.shared_state.power_up_active:
                    self.shared_state.power_up_timer -= 1
                    if self.shared_state.power_up_timer <= 0:
                        self.shared_state.power_up_active = False
                        for ghost in self.ghosts:
                            if not ghost.is_eaten:
                                ghost.is_blue = False

                # Check win condition
                if not any('.' in row or 'e' in row for row in self.board):
                    self.shared_state.win = True

                self.render_frame()
                self.clock.tick(30)

        except Exception as e:
            print(f"Error occurred: {e}")
            self.cleanup()

if __name__ == "__main__":
    game = Game()
    game.start()