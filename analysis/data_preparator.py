import os.path

from .guild_data import GuildData
import pandas as pd

class DataPreparator:
    def __init__(self):
        self.EVENT_LOG_NAME = "event_log.csv"
        self.CONFIG_NAME = "config.json"
        self.GUILD_EVENTS_NAME = "guild_events.jsonl"
        self.MESSAGE_METADATA_NAME = "message_metadata_log.csv"
        self.SESSION_LOG_NAME = "session_log.csv"

    def prepare_data(self, path_to_guild_dir) -> GuildData:
        print('Preparing data for path ' + path_to_guild_dir)
        data_frame = self._load_event_log_csv(path_to_guild_dir)
        data_frame = self._convert_to_pandas_datetime(data_frame)
        guild_id, guild_name, data_frame = self._extract_guild_name_and_id(data_frame)
        member_id_name_map, data_frame = self._create_member_id_name_map(data_frame)
        channel_id_name_map, data_frame = self._create_channel_id_name_map(data_frame)
        data_frame = self._add_synthetic_tracker_column(data_frame)
        data_frame = self._correct_orphan_events(data_frame, member_id_name_map.keys())
        data_frame = self._sort_data_frame(data_frame)

        guild_data = GuildData(data_frame, guild_id, guild_name, member_id_name_map, channel_id_name_map)
        return guild_data

    def _load_event_log_csv(self, dir_path) -> pd.DataFrame:
        event_path = os.path.join(dir_path, self.EVENT_LOG_NAME)
        print(f'Loading data from {event_path}')
        return pd.read_csv(event_path)

    def _convert_to_pandas_datetime(self, data_frame) -> pd.DataFrame:
        print(f'Converting timestamps to pandas datetime')
        data_frame['timestamp'] = pd.to_datetime(data_frame['timestamp'], unit='s')
        return data_frame

    def _extract_guild_name_and_id(self, data_frame) -> tuple:
        print(f'Extracting guild name and id')
        # Getting the last row of the df so we get the last name the server was saved as
        last_row = data_frame.sort_values(by=['timestamp'], ascending=True).tail(1)
        guild_id = last_row['guild_id'].values[0]
        guild_name = last_row['guild_name'].values[0]
        data_frame = data_frame.drop(columns=['guild_id', 'guild_name'])
        return guild_id, guild_name, data_frame

    def _create_member_id_name_map(self, data_frame) -> tuple:
        print(f'Creating member id name map')
        member_id_name_map = {}
        member_ids = data_frame['member_id'].unique()
        member_id_name_map = {}

        for m_id in member_ids:
            df_member = data_frame[data_frame['member_id'] == m_id]
            last_row = df_member.sort_values(by=['timestamp'], ascending=True).tail(1)
            last_known_name = last_row['member_name'].values[0]
            member_id_name_map[m_id] = last_known_name

        data_frame = data_frame.drop(columns=['member_name'])
        return member_id_name_map, data_frame

    def _create_channel_id_name_map(self, data_frame) -> tuple:
        print(f'Creating channel id name map')
        channel_ids = data_frame['channel_id'].unique()
        channel_id_name_map = {}

        for c_id in channel_ids:
            df_channel = data_frame[data_frame['channel_id'] == c_id]
            last_row = df_channel.sort_values(by=['timestamp'], ascending=True).tail(1)
            last_known_name = last_row['channel_name'].values[0]
            channel_id_name_map[c_id] = last_known_name

        data_frame = data_frame.drop(columns=['channel_name'])
        return channel_id_name_map, data_frame

    def _add_synthetic_tracker_column(self, data_frame) -> pd.DataFrame:
        data_frame.insert(loc=4, column='synthetic', value=False)
        return data_frame

    def _insert_row(self, data_frame, member_id, timestamp, channel_id, event_type):

        if event_type == 'join':
            timestamp -= pd.Timedelta(seconds=1)
        else:
            timestamp += pd.Timedelta(seconds=1)

        new_row = pd.DataFrame([{
            'member_id': member_id,
            'timestamp': timestamp,
            'channel_id': channel_id,
            'event_type': event_type,
            'synthetic': True,
        }])

        return pd.concat([data_frame, new_row], ignore_index=True)

    def _correct_orphan_joins_for_member(self, data_frame, df_member):
        # We expect every df to start with a join
        expected_type = 'join'
        df_member.reset_index(inplace=True)
        rows = 0
        for idx, row in df_member.iterrows():
            rows += 1
            actual_type = row['event_type']
            # If the types match we can swap the expected type and move on
            if actual_type == expected_type:
                if expected_type == 'join':
                    expected_type = 'leave'
                else:
                    expected_type = 'join'
            else:
                # If they dont we insert the missing event in our original df
                data_frame = self._insert_row(data_frame, row['member_id'], row['timestamp'], row['channel_id'], expected_type)

        # This essentially means we are missing a leave event at the end that is not being caught since the for loop simply terminates
        if rows % 2 == 1 and expected_type == 'leave':
            last_row = df_member.tail(1).iloc[0]
            data_frame = self._insert_row(data_frame, last_row['member_id'], last_row['timestamp'], last_row['channel_id'], expected_type)

        return data_frame


    def _correct_orphan_events(self, data_frame, member_ids):
        print(f'Checking entire dataframe for orphaned events')
        df_copy = data_frame.copy(deep=True)

        for m_id in member_ids:
            df_member = df_copy[df_copy['member_id'] == m_id]
            data_frame = self._correct_orphan_joins_for_member(data_frame, df_member)

        return data_frame

    def _sort_data_frame(self, data_frame) -> pd.DataFrame:
        data_frame['event_order'] = (
                data_frame['event_type'] == 'join'
        ).astype(int)

        data_frame = data_frame.sort_values(by=['timestamp', 'event_order'])

        data_frame = data_frame.drop(columns=['event_order'])

        data_frame = data_frame.reset_index(drop=True)

        return data_frame