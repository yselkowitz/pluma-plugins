import commander.commands as commands
import commander.commands.exceptions

import types
import gtksourceview2 as gsv

__commander_module__ = True

def _complete_options(words, idx):
	ret = []

	gb = globals()

	for k in gb:
		if type(gb[k]) == types.FunctionType and not k.startswith('_'):
			ret.append(k.replace('_', '-'))

	ret.sort()
	return commands.completion.words(ret)(words, idx)

def _complete_language(words, idx):
	manager = gsv.language_manager_get_default()
	ids = manager.get_language_ids()
	ids.append('none')
	ids.sort()

	return commands.completion.words(ids)(words, idx)

def _complete_use_spaces(words, idx):
	return commands.completion.words(['yes', 'no'])(words, idx)

def _complete_draw_spaces(words, idx):
	ret = ['none', 'all', 'tabs', 'newlines', 'nbsp', 'spaces']
	return commands.completion.words(ret)(words, idx)

def _complete_value(words, idx):
	# Depends a bit on the option
	ret, completion = _complete_options(words, idx - 1)

	if not ret:
		return None

	completer = '_complete_' + ret[0].replace('-', '_')
	gb = globals()

	if completer in gb:
		return gb[completer](words[1:], idx - 1)
	else:
		return None

@commands.autocomplete(option=_complete_options, value=_complete_value)
def __default__(view, option, value):
	"""Set pluma option: set &lt;option&gt; &lt;value&gt;

Sets a pluma option, such as document language, or indenting"""

	option = option.replace('-', '_')
	gb = globals()

	if option in gb and type(gb[option]) == types.FunctionType:
		return gb[option](view, value)
	else:
		raise commander.commands.exceptions.Execute('Invalid setting: ' + option)

@commands.autocomplete(language=_complete_language)
def language(view, language=None):
	"""Set document language: set.language &lt;language&gt;

Set the document language to the language with the specified id"""
	if not language or language == 'none':
		view.get_buffer().set_language(None)
		return False

	manager = gsv.language_manager_get_default()
	lang = manager.get_language(language)

	if lang:
		view.get_buffer().set_language(lang)
		return False
	else:
		raise commander.commands.exceptions.Execute('Invalid language: ' + language)

def tab_width(view, width):
	"""Set document tab width: set.tab-width &lt;width&gt;

Set the document tab width"""

	try:
		width = int(width)
	except:
		raise commander.commands.exceptions.Execute("Invalid tab width: " + str(width))

	if width <= 0:
		raise commander.commands.exceptions.Execute("Invalid tab width: " + str(width))

	view.set_tab_width(width)
	return False

tab_size = tab_width

@commands.autocomplete(value=_complete_use_spaces)
def use_spaces(view, value):
	"""Use spaces instead of tabs: set.use-spaces &lt;yes/no&gt;

Set to true/yes to use spaces instead of tabs"""

	setting = value in ('yes', 'true', '1')
	view.set_insert_spaces_instead_of_tabs(setting)

	return False

@commands.autocomplete({'*': _complete_draw_spaces})
def draw_spaces(view, *args):
	"""Draw spaces: set.draw-spaces &lt;none/all/tabs/newlines/nbsp/spaces&gt;

Set what kind of spaces should be drawn. Multiple options can be defined, e.g.
for drawing spaces and tabs: <i>set.draw-spaces space tab</i>"""
	m = {
		'none': 0,
		'all': gsv.DRAW_SPACES_ALL,
		'tabs': gsv.DRAW_SPACES_TAB,
		'newlines': gsv.DRAW_SPACES_NEWLINE,
		'nbsp': gsv.DRAW_SPACES_NBSP,
		'spaces': gsv.DRAW_SPACES_SPACE
	}

	flags = 0

	for arg in args:
		for a in m:
			if a.startswith(arg):
				flags = flags | m[a]

	view.set_draw_spaces(flags)
	return False
