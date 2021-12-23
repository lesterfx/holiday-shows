from enum import IntEnum

class PLAYER_KINDS(IntEnum):
    MUSIC = 1
    STRIP = 2

class Players(dict):
    def play_all(self, arguments):
        players = []
        for player in self.values():
            players.append(player.play(arguments))
        while True:
            still_going = False
            for player in players:
                try:
                    yield next(player)
                    still_going = True
                except StopIteration:
                    pass
            if not still_going:
                break
        print(f'all {len(players)} players finished')

    def add(self, player_kind, player_globals):
        print('Adding player', player_kind, 'with globals', player_globals)
        if player_kind == PLAYER_KINDS.MUSIC:
            from . import music_player
            self[PLAYER_KINDS.MUSIC] = music_player.Music_Player(player_globals)
        elif player_kind == PLAYER_KINDS.STRIP:
            from . import strip_player
            self[PLAYER_KINDS.STRIP] = strip_player.Strip_Player(player_globals)
        else:
            raise ValueError(f'Unknown player kind: {player_kind}')

    def load_data(self, player_kind, data):
        self[player_kind].load_data(data)
