import pygame

delta: int = -1
ticks: int = -1


def update() -> None:
    global delta, ticks
    delta = ticks
    ticks = pygame.time.get_ticks()


def get_time() -> int:
    return ticks


def get_variation() -> int:
    return ticks - delta
