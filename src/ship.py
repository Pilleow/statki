import pygame


class Ship:
    def __init__(self, sprite: object, pos: list, length: int, direction: int):
        self.pos = pos
        self.sprite_original = sprite
        self.sprite = sprite
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
        self.sprite = pygame.transform.rotate(self.sprite_original, -self.direction)


    def draw(self, display: object, bd_pos, bd_scale):
        pos = [p * bd_scale for p in self.pos]
        if self.direction == 0:
            pos[1] -= (self.length - 1) * bd_scale
        elif self.direction == 270:
            pos[0] -= (self.length - 1) * bd_scale
        display.blit(self.sprite, self._translate(pos, bd_pos))
        '''
        for r in self.parts:
            pos = self._translate([p * bd_scale for p in r[0]], bd_pos)
            pygame.draw.rect(display, [255, 0, 0], [pos[0], pos[1], bd_scale, bd_scale], 1)
        '''

    @staticmethod
    def _translate(v1: list, v2: list) -> list:
        return [v1[i] + v2[i] for i in range(len(v1))]