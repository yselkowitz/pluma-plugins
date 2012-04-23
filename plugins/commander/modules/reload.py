import commander.commands
import commander.commands.completion
import commander.commands.exceptions
import commander.commands.result
import commander.utils as utils
import commander.commands.module

__commander_module__ = True

@commander.commands.autocomplete(command=commander.commands.completion.command)
def __default__(command):
	"""Force reload of a module: reload &lt;module&gt;

Force a reload of a module. This is mostly useful on systems where file monitoring
does not work correctly."""

	# Get the command
	res = commander.commands.completion.command([command], 0)

	if not res:
		raise commander.commands.exceptions.Execute('Could not find command: ' + command)

	mod = res[0][0]

	while not isinstance(mod, commander.commands.module.Module):
		mod = mod.parent

	commander.commands.Commands().reload_module(mod)
	return commander.commands.result.DONE