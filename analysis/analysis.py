import os

import pandas as pd

from .data_preparator import DataPreparator
from .guild_data import GuildData

class Analyzer:
    def __init__(self):
        self._data_preparator = DataPreparator()

    def analyze(self, path_to_guild_dir):
        guild_data = self._data_preparator.prepare_data(path_to_guild_dir)

        print(guild_data)
        return guild_data

    def analyze_guild_stats(self, guild_data):
        pass



