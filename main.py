# main.py — ponto de entrada do sistema de navegacao por algoritmos de busca
# execute com: python3 main.py

from gui.interface import AplicacaoNavegacao


def principal() -> None:
    app = AplicacaoNavegacao()
    app.executar()


if __name__ == "__main__":
    principal()
