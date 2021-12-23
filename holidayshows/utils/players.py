from enum import IntEnum

class PLAYER_KINDS(IntEnum):
    MUSIC = 1
    STRIP = 2

class Players(dict):
    def play_all(self, arguments):
        players = []
        for player in self.values():
            players.append(player.play(arguments))
        for player in players:
            yield
            try:
                next(player)
            except StopIteration:
                pass
        print(f'all {len(players)} players finished')

    def add(self, player_kind, player_globals):
        print('Adding player', player_kind, 'with globals', player_globals)
        if player_kind == PLAYER_KINDS.MUSIC:
            from . import music_player
            self[PLAYER_KINDS.MUSIC] = music_player.Music_Player(player_globals)
        elif player_kind == PLAYER_KINDS.STRIP:
            from . import strip_cache_player
            self[PLAYER_KINDS.STRIP] = strip_cache_player.Strip_Cache_Player(player_globals)
        else:
            raise ValueError(f'Unknown player kind: {player_kind}')

    def load_data(self, player_kind, data):
        self[player_kind].load_data(data)
