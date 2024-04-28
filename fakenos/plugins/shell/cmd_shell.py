"""
Custom shell class to interact with NOS.
"""

from cmd import Cmd
import logging
import traceback
import copy

log = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class CMDShell(Cmd):
    """
    Custom shell class to interact with NOS.
    """

    use_rawinput = False

    commands = {
        "exit": {"output": True, "help": "Exit commands shell"},
        "_default_": {
            "output": "Unknown command",
            "help": "Output to print for unknown commands",
        },
    }

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        stdin,
        stdout,
        nos,
        nos_inventory_config,
        base_prompt,
        is_running,
        intro="Custom SSH Shell",
        ruler="",
        completekey="tab",
        newline="\r\n",
    ):
        self.nos = nos
        self.ruler = ruler
        self.intro = intro
        self.base_prompt = base_prompt
        self.newline = newline
        self.prompt = nos.initial_prompt.format(base_prompt=base_prompt)
        self.is_running = is_running

        # form commands
        self.commands = {
            **copy.deepcopy(self.commands),
            **copy.deepcopy(nos.commands or {}),
            **copy.deepcopy(nos_inventory_config.get("commands", {})),
        }

        # call the base constructor of cmd.Cmd, with our own stdin and stdout
        super().__init__(
            completekey=completekey,
            stdin=stdin,
            stdout=stdout,
        )

    def start(self):
        """Method to start the shell"""
        self.cmdloop()

    def stop(self):
        """Method to stop the shell"""
        self.stdin.write("exit" + self.newline)

    def writeline(self, value):
        """Method to write a line to stdout with newline at the end"""
        for line in str(value).splitlines():
            self.stdout.write(line + self.newline)

    def emptyline(self):
        """This method to do nothing if empty line entered"""

    def precmd(self, line):
        return line

    # pylint: disable=unused-argument
    def postcmd(self, stop, line):
        """Method to return stop value to stop the shell"""
        return stop

    # pylint: disable=unused-argument
    def do_help(self, arg):
        """Method to return help for commands"""
        lines = {}  # dict of {cmd: cmd_help}
        width = 0  # record longest command width for padding
        # form help for all commands
        for cmd, cmd_data in self.commands.items():
            # skip special commands
            if cmd.startswith("_") and cmd.endswith("_"):
                continue
            # skip commands that does not match current prompt
            if not self._check_prompt(cmd_data.get("prompt")):
                continue
            lines[cmd] = cmd_data.get("help", "")
            width = max(width, len(cmd))
        # form help lines
        help_msg = []
        for k, v in lines.items():
            padding = " " * (width - len(k)) + "  "
            help_msg.append(f"{k}{padding}{v}")
        self.writeline(self.newline.join(help_msg))

    def _check_prompt(self, prompt_):
        """
        Helper method to check if prompt_ matches current prompt

        :param prompt_: (string or None)  prompt to check
        """
        # prompt_ is None if no 'prompt' key defined for command
        if prompt_ is None:
            return True
        if isinstance(prompt_, str):
            return self.prompt == prompt_.format(base_prompt=self.base_prompt)
        if isinstance(prompt_, list):
            return any(self.prompt == i.format(base_prompt=self.base_prompt) for i in prompt_)
        return False

    def default(self, line):
        """Method called if no do_xyz methods found"""
        log.debug("shell.default '%s' running command '%s'", self.base_prompt, [line])
        ret = self.commands["_default_"]["output"]
        try:
            cmd_data = self.commands[line]
            if "alias" in cmd_data:
                cmd_data = {**self.commands[cmd_data.pop("alias")], **cmd_data}
            if self._check_prompt(cmd_data.get("prompt")):
                ret = cmd_data["output"]
                if callable(ret):
                    ret = ret(
                        base_prompt=self.base_prompt,
                        current_prompt=self.prompt,
                        command=line,
                    )
                    if isinstance(ret, dict):
                        if "new_prompt" in ret:
                            self.prompt = ret["new_prompt"].format(base_prompt=self.base_prompt)
                        ret = ret["output"]
                if "new_prompt" in cmd_data:
                    self.prompt = cmd_data["new_prompt"].format(base_prompt=self.base_prompt)
            else:
                log.warning("'%s' command prompt '%s' not matching current prompt '%s'", line, cmd_data.get("prompt", "").format(base_prompt=self.base_prompt), self.prompt)
        except KeyError:
            log.error("shell.default '%s' command '%s' not found", self.base_prompt, [line])
        # pylint: disable=broad-except
        except (Exception,) as e:
            log.error("An error occurred: %s", str(e))
            ret = traceback.format_exc()
            ret = ret.replace("\n", self.newline)
        # check if need to exit
        if ret is True or not self.is_running.is_set():
            return True
        if ret is not None:
            ret = ret.format(base_prompt=self.base_prompt)
            self.writeline(ret)
        return False
