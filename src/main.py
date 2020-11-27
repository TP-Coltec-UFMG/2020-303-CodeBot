import pygame
import gui


def main():
    def draw_this():
        screen.fill((0, 0, 0, 0))
        ui.draw(screen, screen.get_clip())
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    xml = gui.LoaderXML("res/test.xml")
    ui = xml.get_tree()
    # ui.tree_print()
    # draw_this()
    while True:
        draw_this()
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return


if __name__ == "__main__":
    main()
