import pygame
import ticks


class Game:
    def __init__(self):
        self.block_dragged = None
        self.click_start = -1

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.click_start = ticks.get_time()
        elif event.type == pygame.MOUSEBUTTONUP:
            click_duration = ticks.get_time() - self.click_start
            print(click_duration)


class Blocklist:
    pass


class Codeblock:
    pass
