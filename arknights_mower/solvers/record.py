# 用于记录Mower操作行为
import sqlite3
import os
from collections import defaultdict

from arknights_mower.utils.log import logger
from datetime import datetime, timezone


# 记录干员进出站以及心情数据，将记录信息存入agent_action表里
def save_action_to_sqlite_decorator(func):
    def wrapper(self, name, mood, current_room, current_index, update_time=False):
        agent = self.operators[name]  # 干员

        agent_current_room = agent.current_room  # 干员所在房间
        agent_is_high = agent.is_high()  # 是否高优先级

        # 调用原函数
        result = func(self, name, mood, current_room, current_index, update_time)

        # 保存到数据库
        current_time = datetime.now()
        database_path = os.path.join('tmp', 'data.db')

        try:
            # Create 'tmp' directory if it doesn't exist
            os.makedirs('tmp', exist_ok=True)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            # Create a table if it doesn't exist
            cursor.execute('CREATE TABLE IF NOT EXISTS agent_action ('
                           'name TEXT,'
                           'agent_current_room TEXT,'
                           'current_room TEXT,'
                           'is_high INTEGER,'
                           'agent_group TEXT,'
                           'mood INTEGER,'
                           'current_time TEXT'
                           ')')

            # Insert data
            cursor.execute('INSERT INTO agent_action VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (name, agent_current_room, current_room, int(agent_is_high), agent.group, int(mood),
                            str(current_time)))

            connection.commit()
            connection.close()

            # Log the action
            logger.debug(
                f"Saved action to SQLite: Name: {name}, Agent's Room: {agent_current_room}, Agent's group: {agent.group}, "
                f"Current Room: {current_room}, Is High: {agent_is_high}, Current Time: {current_time}")

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")

        return result

    return wrapper


def get_work_rest_ratios():
    # TODO 整理数据计算工休比
    database_path = os.path.join('tmp', 'data.db')
    # 连接到数据库
    # conn = sqlite3.connect(database_path)
    conn = sqlite3.connect('../../tmp/data.db')
    cursor = conn.cursor()

    # 查询数据
    cursor.execute("SELECT a.* FROM agent_action a "
                   "where DATE(a.current_time) >= DATE('now', '-1 day','localtime')"
                   "and is_high = 1 order by a.current_time ")
    data = cursor.fetchall()

    # 关闭数据库连接
    conn.close()

    # print(data)
    return data


# 整理心情曲线
def get_mood_ratios():
    database_path = os.path.join('tmp', 'data.db')

    try:
        # 连接到数据库
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        # 查询数据（筛掉宿管和替班组的数据）
        cursor.execute("""
                        SELECT a.* FROM agent_action a 
                       where DATE(a.current_time) >= DATE('now', '-7 day','localtime')
                       and a.name in (select distinct b.name 
                                from agent_action b where DATE(a.current_time) >= DATE('now', '-7 day','localtime')
                                and b.is_high = 1 and b.current_room not like 'dormitory%')
                       order by a.agent_group desc, a.current_time 
                       """)
        data = cursor.fetchall()
        # 关闭数据库连接
        conn.close()
    except sqlite3.Error as e:
        data = []

    grouped_data = {}
    for row in data:
        group_name = row[4]  # Assuming 'agent_group' is at index 4
        if not group_name:
            group_name = row[0]
        mood_data = grouped_data.get(group_name, {
            'labels': [],
            'datasets': []
        })

        timestamp_datetime = datetime.strptime(row[6], '%Y-%m-%d %H:%M:%S.%f')  # Assuming 'current_time' is at index 6
        # 创建 Luxon 格式的字符串
        current_time = f"{timestamp_datetime.year:04d}-{timestamp_datetime.month:02d}-{timestamp_datetime.day:02d}T{timestamp_datetime.hour:02d}:{timestamp_datetime.minute:02d}:{timestamp_datetime.second:02d}.{timestamp_datetime.microsecond:06d}+08:00"

        mood_label = row[0]  # Assuming 'name' is at index 0
        mood_value = row[5]  # Assuming 'mood' is at index 5

        if mood_label in [dataset['label'] for dataset in mood_data['datasets']]:
            # if mood_label == mood_data['datasets'][0]['label']:
            mood_data['labels'].append(current_time)
            # If mood label already exists, find the corresponding dataset
            for dataset in mood_data['datasets']:
                if dataset['label'] == mood_label:
                    dataset['data'].append({'x': current_time, 'y': mood_value})
                    break
        else:
            # If mood label doesn't exist, create a new dataset
            mood_data['labels'].append(current_time)
            mood_data['datasets'].append({
                'label': mood_label,
                'data': [{'x': current_time, 'y': mood_value}]
            })

        grouped_data[group_name] = mood_data

    # 将数据格式整理为数组
    formatted_data = []
    for group_name, mood_data in grouped_data.items():
        formatted_data.append({
            'groupName': group_name,
            'moodData': mood_data
        })

    return formatted_data


def __main__():
    get_mood_ratios()

# __main__()
