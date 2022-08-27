import pygame


class Ship:
    def __init__(self, pos: list, length: int, direction: int):
        self.pos = pos
        self.length = length
        self.direction = direction
        self.changeDirection(direction)

    def isHit(self, hit_pos: list):
        for i, p in enumerate(self.parts):
            if hit_pos == p[0]:
                self.parts[i][1] -= 1
                return True
        return False

    def changePos(self, pos):
        self.pos = pos
        self.parts = []
        for i in range(self.length):
            if self.direction == 0:
                self.parts.append([self._translate(self.pos, [0, -i]), 1])
            elif self.direction == 180:
                self.parts.append([self._translate(self.pos, [0, i]), 1])
            elif self.direction == 270:
                self.parts.append([self._translate(self.pos, [-i, 0]), 1])
            elif self.direction == 90:
                self.parts.append([self._translate(self.pos, [i, 0]), 1])


    def changeDirection(self, direction):
        if direction >= 360:
            direction = direction - 360
        elif direction < 0:
            direction = direction + 360
        self.direction = direction
        self.parts = []
        for i in range(self.length):
            if direction == 0:
                self.parts.append([self._translate(self.pos, [0, -i]), 1])
            elif direction == 180:
                self.parts.append([self._translate(self.pos, [0, i]), 1])
            elif direction == 270:
                self.parts.append([self._translate(self.pos, [-i, 0]), 1])
            elif direction == 90:
                self.parts.append([self._translate(self.pos, [i, 0]), 1])


    def draw(self, display: object, bd_pos, bd_scale):
        r = [0, 0, bd_scale - 6, bd_scale - 6]
        for p in self.parts:
            r[0] = bd_pos[0] + p[0][0] * bd_scale + 3
            r[1] = bd_pos[1] + p[0][1] * bd_scale + 3
            pygame.draw.rect(display, [0, 0, 0], r)

    @staticmethod
    def _translate(v1: list, v2: list) -> list:
        return [v1[i] + v2[i] for i in range(len(v1))]