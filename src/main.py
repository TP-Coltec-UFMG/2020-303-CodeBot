import pygame
import gui


def main() -> None:
    clk = pygame.time.Clock()
    pygame.init()
    gui.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    ui = gui.LoaderXML("res/test.xml").get_document()

    ui.root.tree_print()

    while True:
        screen.fill((0, 0, 0, 0))
        ui.root.draw(screen, screen.get_clip())
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

        # Limit framerate so as to not heat up CPU unnecessarily
        clk.tick(20)


if __name__ == "__main__":
    main()
