import re

from mcdreforged.api.all import *

from gamemode.dimension import get_dimension, Dimension, LegacyDimension
from gamemode.position import Position


class Config(Serializable):
	sleep_time: int = 3
	use_rcon_if_possible: bool = True
	user_list: dict = {}
	gamemode: str = 'survival'


config: Config
CONFIG_FILE = 'config/gamemode.json'
gamemode_user = 0


def process_coordinate(text: str) -> Position:
	data = text[1:-1].replace('d', '').split(', ')
	data = [(x + 'E0').split('E') for x in data]
	assert len(data) == 3
	return Position(*[float(e[0]) * 10 ** int(e[1]) for e in data])


def process_dimension(text: str) -> str:
	return text.replace(re.match(r'[\w ]+: ', text).group(), '', 1).strip('"\' ')


def __display(server: ServerInterface, name: str, position: Position, dimension_str: str):
	global config
	x, y, z = position
	dimension = get_dimension(dimension_str)

	userInfo = config.user_list.get(name, None)
	if not userInfo:
		config.user_list[name] = [x, y + 0.5, z, dimension.get_reg_key()]
		server.execute('gamemode spectator')

	server.say(RText('切换模式', RColor.aqua).h('§bGamemode§r: 点击可以切换模式').c(RAction.run_command, '!!gm'))


def display(server: ServerInterface, name: str, position: Position, dimension_str: str):
	try:
		__display(server, name, position, dimension_str)
	except:
		server.logger.exception('Error displaying coordinate information')


def on_info(server: PluginServerInterface, info: Info):
	global gamemode_user
	global config
	if info.is_player and info.content == '!!gm':
		name = info.player
		userInfo = config.user_list.get(name, None)
		if userInfo:
			server.execute('/execute in {} run tp {} {} {}'.format(userInfo[3], userInfo[0], userInfo[1], userInfo[2]))
			server.execute('gamemode {}'.format(config.gamemode))
			del config.user_list[name]
		else:
			if server.is_rcon_running() and config.use_rcon_if_possible:
				position = process_coordinate(re.search(r'\[.*]', server.rcon_query('data get entity {} Pos'.format(name))).group())
				dimension = process_dimension(server.rcon_query('data get entity {} Dimension'.format(name)))
				display(server, name, position, dimension)
			else:
				gamemode_user += 1
				server.execute('data get entity ' + info.player)
	if not info.is_player and gamemode_user > 0 and re.match(r'\w+ has the following entity data: ', info.content) is not None:
		name = info.content.split(' ')[0]
		dimension = re.search(r'(?<= Dimension: )(.*?),', info.content).group().replace('"', '').replace("'", '').replace(',', '')
		position_str = re.search(r'(?<=Pos: )\[.*?]', info.content).group()
		position = process_coordinate(position_str)
		display(server, name, position, dimension)
		gamemode_user -= 1


def on_load(server: PluginServerInterface, old):
	server.register_help_message('!!gamemode', '切换旁观和生存')
	global config
	config = server.load_config_simple(CONFIG_FILE, target_class=Config, in_data_folder=False)
