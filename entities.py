class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = "player"

    def move(self, direction):
        if direction == "left":
            self.x -= 1
        elif direction == "right":
            self.x += 1
        elif direction == "up":
            self.y -= 1
        elif direction == "down":
            self.y += 1


class Ghost:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = "ghost"
        self.is_blue = False  # Ghosts turn blue when Pacman eats an energizer

    def move(self, direction):
        if direction == "left":
            self.x -= 1
        elif direction == "right":
            self.x += 1
        elif direction == "up":
            self.y -= 1
        elif direction == "down":
            self.y += 1


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = "dot"
        self.points = 10


class Energizer:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = "energizer"
        self.points = 50


class Fruit:
    def __init__(self, x, y, fruit_name):
        self.x = x
        self.y = y
        self.type = "fruit"
        self.fruit_type = fruit_name
        self.points = self.initialize_points(self.fruit_type)

    def initialize_points(self, fruit):
        score_sheet = {
            "cherry": 200,
            "strawberry": 300,
            "orange": 500,
            "apple": 700,
            "melon": 1000
        }
        return score_sheet.get(fruit, 0)
