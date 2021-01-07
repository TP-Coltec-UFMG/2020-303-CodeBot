import pygame
from pygame.image import load_extended
import ticks
import yaml
import math


class Level:
    def __init__(self, filename: str):
        text: str
        with open(filename, encoding='utf-8') as file:
            text = file.read()
            # print(text)
        data = yaml.safe_load(text)
        # Available blocks
        self.blocks = data["blocks"]


class Game:
    def __init__(self):
        self.block_dragged = None
        self.click_start = -1
        self.sprite: pygame.Surface = load_extended("res/textures/go_back.png")

    def handle_event(self, _: pygame.Surface, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.click_start = ticks.get_time()
        elif event.type == pygame.MOUSEBUTTONUP:
            click_duration = ticks.get_time() - self.click_start
            print(click_duration)

    def render(self, screen: pygame.Surface, angle_x: float, angle_y: float):
        transformed = pygame.transform.rotate(self.sprite, math.degrees(angle_x))
        transformed = pygame.transform.scale(
            transformed,
            (int(transformed.get_width()),
             int(transformed.get_height() * math.sin(angle_y)))
        )
        pos_x, pos_y = 200 - int(transformed.get_width()) / 2, 200 - int(transformed.get_height()) / 2
        screen.blit(transformed, (pos_x, pos_y))


class Blocklist:
    def __init__(self):
        pass

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("click! " + self.__str__())


class Codeblock:
    pass
