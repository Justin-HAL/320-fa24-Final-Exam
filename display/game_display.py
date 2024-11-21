import pygame

def render_board(board, player, ghosts):
    pygame.init()
    screen = pygame.display.set_mode((560, 720))  # 20px per cell
    clock = pygame.time.Clock()

    running = True
    while running:
        screen.fill((0, 0, 0))  # Black background
        for y, row in enumerate(board):
            for x, cell in enumerate(row):
                if player.x == x and player.y == y:
                    pygame.draw.rect(screen, (255, 255, 0), (x * 20, y * 20, 20, 20))  # Yellow for player
                elif any(ghost.x == x and ghost.y == y for ghost in ghosts):
                    pygame.draw.rect(screen, (255, 0, 0), (x * 20, y * 20, 20, 20))  # Red for ghosts
                elif cell and cell.type == "dot":
                    pygame.draw.circle(screen, (255, 255, 255), (x * 20 + 10, y * 20 + 10), 3)  # White dots

        pygame.display.flip()
        clock.tick(60)
