from game import PLAYER_O, PLAYER_X, TicTacToe


def test_horizontal_win():
    game = TicTacToe()
    moves = [(0, PLAYER_X), (3, PLAYER_O), (1, PLAYER_X), (4, PLAYER_O), (2, PLAYER_X)]
    for pos, player in moves:
        game.make_move(pos, player)
    assert game.winner == PLAYER_X
    assert game.winning_line == [0, 1, 2]
    assert game.is_over()


def test_draw():
    game = TicTacToe()
    # X O X / X O O / O X X -> no winner, board full
    moves = [
        (0, PLAYER_X), (1, PLAYER_O), (2, PLAYER_X),
        (4, PLAYER_O), (3, PLAYER_X), (5, PLAYER_O),
        (7, PLAYER_X), (6, PLAYER_O), (8, PLAYER_X),
    ]
    for pos, player in moves:
        game.make_move(pos, player)
    assert game.winner is None
    assert game.is_draw()
    assert game.is_over()


def test_rejects_move_out_of_turn():
    game = TicTacToe()
    game.make_move(0, PLAYER_X)
    try:
        game.make_move(1, PLAYER_X)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_rejects_occupied_cell():
    game = TicTacToe()
    game.make_move(0, PLAYER_X)
    try:
        game.make_move(0, PLAYER_O)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_ai_never_loses():
    # AI (O) should always force at least a draw against optimal-ish X play,
    # here we just verify it blocks an immediate winning threat.
    game = TicTacToe()
    game.make_move(0, PLAYER_X)
    game.make_move(4, PLAYER_O)
    game.make_move(1, PLAYER_X)  # X threatens to win at position 2
    move = game.best_move(PLAYER_O)
    assert move == 2


def test_ai_takes_winning_move():
    game = TicTacToe()
    game.board = [PLAYER_O, PLAYER_O, "", PLAYER_X, PLAYER_X, "", "", "", ""]
    game.current_player = PLAYER_O
    move = game.best_move(PLAYER_O)
    assert move == 2
