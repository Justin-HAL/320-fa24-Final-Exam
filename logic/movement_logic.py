def move_entity(entity, direction, board):
    """Move the entity in the given direction if the position is valid."""
    new_x, new_y = entity.x, entity.y
    if direction == "left":
        new_x -= 1
    elif direction == "right":
        new_x += 1
    elif direction == "up":
        new_y -= 1
    elif direction == "down":
        new_y += 1

    if 0 <= new_x < len(board[0]) and 0 <= new_y < len(board) and board[new_y][new_x] is None:
        entity.x, entity.y = new_x, new_y
