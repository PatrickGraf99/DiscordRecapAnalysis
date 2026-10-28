import pandas as pd
from .exceptions import NoSuchIDError

class GuildData:
    """
    Represents data for one guild with the events being stored as a pandas DataFrame
    """
    def __init__(self, event_data: pd.DataFrame, guild_id: int, guild_name: str, member_id_name_map: dict[int, str],
                 channel_id_name_map: dict[int, str]):
        self.event_data: pd.DataFrame = event_data
        self.guild_id: int = guild_id
        self.guild_name: str = guild_name
        self.member_id_name_map: dict[int, str] = member_id_name_map
        self.channel_id_name_map: dict[int, str] = channel_id_name_map

    def __str__(self):
        return (f'Viewing data for guild {self.guild_name} (ID: {self.guild_id})\n'
              f'Guild has {len(self.member_id_name_map)} members and {len(self.channel_id_name_map)} channels\n'
              f'Event log has {self.event_data.shape[0]} events\n')

    def __repr__(self):
        return self.__str__()

    def get_event_data(self) -> pd.DataFrame:
        return self.event_data

    def get_guild_id(self) -> int:
        return self.guild_id

    def get_guild_name(self) -> str:
        return self.guild_name

    def get_member_name(self, member_id: int) -> str:
        """
        :param member_id: The ID of the wanted member
        :return: The member name for the specified member_id
        :raise NoSuchIDError: Raises NoSuchIDError if the ID is not found in the member_id_map
        """
        if member_id in self.member_id_name_map:
            return self.member_id_name_map[member_id]
        raise NoSuchIDError(f'Member with ID {member_id} was not found in guild {self.guild_name}')

    def get_channel_name(self, channel_id: int) -> str:
        """
        :param channel_id: The ID of the wanted channel
        :return: The channel name for the specified channel_id
        :raise NoSuchIDError: Raises NoSuchIDError if the ID is not found in the channel_id_map
        """
        if channel_id in self.channel_id_name_map:
            return self.channel_id_name_map[channel_id]
        raise NoSuchIDError(f'Channel with ID {channel_id} was not found in guild {self.guild_name}')