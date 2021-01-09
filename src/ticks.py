import pygame

delta = -1
ticks = -1


def update():
    global delta, ticks
    delta = ticks
    ticks = pygame.time.get_ticks()


def get_time():
    return ticks


def get_variation():
    return ticks - delta
