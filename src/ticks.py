import pygame

ticks = -1


def update():
    global ticks
    ticks = pygame.time.get_ticks()


def get_time():
    global ticks
    return ticks
