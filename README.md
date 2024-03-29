# CodeBot
![Language/biblioteca](https://img.shields.io/badge/Python-pygames-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

<p align="center">
  <img src="wiki-imgs/menu.png" alt="Menu inicial" width="500">
</p>
<p align="center">Jogo educativo e acessível para auxiliar no aprendizado da programação.</p>

## O que é o CodeBot?
Jogo com o intuito de levar os jogadores a desenvolverem e/ou aprimorarem a sua capacidade lógica, o CodeBot utiliza conceitos de programação em blocos que torna mas abstrato os conceitos de programação, permitindo que qualquer pessoa jogue o jogo sem a necessidade de conhecimentos prévios.

## Programação em blocos
Nosso jogo utiliza o conceito de programação em blocos para realizar as ações feitas pelo robozinho **Rivaldo**. Para isso existem blocos de ação que são dados ao usuário a cada nível alcançado, e esses mesmos blocos dão diversos tipos de interpretações e soluções em algumas fases. Vale resaltar aqui que o jogo se inspirou muito em jogos como Scrath, Doodles e Algorithm City, para a sua construção, entretanto toda engine do CodeBot foi feita praticamente do zero, utilizando de base a biblioteca **Pygames**.

<p align="center">
  <img src="wiki-imgs/programacaoEmBlocos.png" alt="Programação em Blocos" width="500" />
</p>

## Diferenciais do Jogo

O CodeBot vem equipado com um sistema de escolha de idiomas (para maior acessibilidade) e de escolhas de tamanho de legenda, além de ser extremamente intuitivo com o uso de blocos de código: o jogador - iniciante em programação - não precisará programar diretamente em texto, e sim montando seu algoritmo bloco por bloco, tendo também recursos visuais que facilitam a interpretação do problema pelo jogador, como por exemplo, a projeção 3d do mapa.

<p align="center">
  <img src="wiki-imgs/mapa3d.gif" alt="Mapa 3d" width="500"/>
</p>

## Criadores:
- [Edson Paschoal](https://github.com/sshEdd1e)
- [Ezequias Kluyvert](https://github.com/UserZeca)
- [João Pedro Camargo](https://github.com/CommonHooman)
- [Marcus Vinícius](https://github.com/MarcusPeixe)

---

## Instalação:

Antes de instalar o jogo, tenha certeza de que a máquina possui:
- [Git](https://git-scm.com/), para ter acesso ao código fonte do projeto no GitHub.
- [Pip 3](https://pypi.org/project/pip/), para instalar as dependências do código.
- [Python 3](https://www.python.org/), para rodar o código.

### Pela linha de comandos:

Linux (bash):
```bash
# Clonar o repositório para a pasta ./codebot/
$ git clone https://github.com/TP-Coltec-UFMG/codebot

# Instalar as dependências do projeto
$ pip3 install --requirement codebot/requirements.txt

# Abrir o diretório de trabalho
$ cd codebot/

# Executar o script principal
$ python3 src/main.py
```

Windows (powershell):
```powershell
# Clonar o repositório para a pasta ./codebot/
$ git.exe clone https://github.com/TP-Coltec-UFMG/codebot

# Instalar as dependências do projeto
$ pip.exe install --requirement .\codebot\requirements.txt

# Abrir o diretório de trabalho
$ cd .\codebot\

# Executar o script principal
$ python.exe .\src\main.py
```

Tenha certeza de que a versão de Python que está sendo executada é a versão 3.x:
```powershell
$ python --version
# Python 3.8.2
```

---
## Licença
[MIT License](./LICENSE) © [CodeBot](https://github.com/TP-Coltec-UFMG/CodeBot)
