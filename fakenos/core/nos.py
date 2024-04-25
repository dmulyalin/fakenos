"""
Network Operating Systems (NOS). Base class to build NOS plugins instances to use with FakeNOS.
"""

import logging
from typing import Optional
import importlib.util

import yaml

from fakenos.core.pydantic_models import ModelNosAttributes

log = logging.getLogger(__name__)

available_platforms: list[str] = [
    "alcatel_aos",
    "alcatel_sros",
    "allied_telesis_awplus",
    "arista_eos",
    "aruba_os",
    "avaya_ers",
    "avaya_vsp",
    "broadcom_icos",
    "brocade_netiron",
    "checkpoint_gaia",
    "cisco_asa",
    "cisco_ftd",
    "cisco_ios",
    "cisco_nxos",
    "cisco_s300",
    "cisco_xr",
    "dell_force10",
    "dlink_ds",
    "eltex",
    "ericsson_ipos",
    "extreme_exos",
    "hp_comware",
    "hp_procurve",
    "huawei_smartax",
    "huawei_vrp",
    "ipinfusion_ocnos",
    "juniper_junos",
    "linux",
    "ubiquiti_edgerouter",
    "ubiquiti_edgeswitch",
    "vyatta_vyos",
    "yamaha",
    "zyxel_os",
]


class Nos:
    """
    Base class to build NOS plugins instances to use with FakeNOS.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        name: str = "FakeNOS",
        commands: dict = None,
        initial_prompt: str = "FakeNOS>",
        filename: Optional[str] = None,
        dict_args: Optional[dict] = None,
    ) -> None:
        """
        Method to instantiate Nos Instance

        :param name: NOS plugin name
        :param commands: dictionary of NOS commands
        :param initial_prompt: NOS initial prompt
        """
        self.name = name
        self.commands = commands or {}
        self.initial_prompt = initial_prompt
        if filename:
            print("HOLA")
            self.from_file(filename)
        elif dict_args:
            self.from_dict(dict_args)

        self.validate()

    def validate(self) -> None:
        """
        Method to validate NOS attributes: commands, name,
        initial prompt - using Pydantic models,
        raises ValidationError on failure.
        """
        ModelNosAttributes(**self.__dict__)
        log.debug("%s NOS attributes validation succeeded", self.name)

    def from_dict(self, data: dict) -> None:
        """
        Method to build NOS from dictionary data.

        Sample NOS dictionary::

            nos_plugin_dict = {
                "name": "MyFakeNOSPlugin",
                "initial_prompt": "{base_prompt}>",
                "commands": {
                    "terminal width 511": {
                        "output": "",
                        "help": "Set terminal width to 511",
                        "prompt": "{base_prompt}>",
                    },
                    "terminal length 0": {
                        "output": "",
                        "help": "Set terminal length to 0",
                        "prompt": "{base_prompt}>",
                    },
                    "show clock": {
                        "output": "MyFakeNOSPlugin system time is 00:00:00",
                        "help": "Show system time",
                        "prompt": "{base_prompt}>",
                    },
                },
            }

        :param data: NOS dictionary
        """
        self.name = data.get("name", self.name)
        self.commands = data.get("commands", self.commands)
        self.initial_prompt = data.get("initial_prompt", self.initial_prompt)

    def from_yaml(self, data: str) -> None:
        """
        Method to build NOS from YAML data.

        Sample NOS YAML file content::

            name: "MyFakeNOSPlugin"
            initial_prompt: "{base_prompt}>"
            commands:
                terminal width 511: {
                    "output": "",
                    "help": "Set terminal width to 511",
                    "prompt": "{base_prompt}>",
                }
                terminal length 0: {
                    "output": "",
                    "help": "Set terminal length to 0",
                    "prompt": "{base_prompt}>",
                }
                show clock: {
                    "output": "MyFakeNOSPlugin system time is 00:00:00",
                    "help": "Show system time",
                    "prompt": "{base_prompt}>",
                }

        :param data: YAML structured text
        """
        with open(data, "r", encoding="utf-8") as f:
            self.from_dict(yaml.safe_load(f))

    def from_module(self, data: str) -> None:
        """
        Method to import NOS data from python file.

        Load the .py using the recipe:
        https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly

        Sample Python NOS plugin file::

            name = "MyFakeNOSPlugin"

            INITIAL_PROMPT = "{base_prompt}>"

            commands = {
                "terminal width 511": {
                    "output": "",
                    "help": "Set terminal width to 511",
                    "prompt": "{base_prompt}>",
                },
                "terminal length 0": {
                    "output": "",
                    "help": "Set terminal length to 0",
                    "prompt": "{base_prompt}>",
                },
                "show clock": {
                    "output": "MyFakeNOSPlugin system time is 00:00:00",
                    "help": "Show system time",
                    "prompt": "{base_prompt}>",
                },
            }

        :param data: OS path string to Python .py file
        """
        spec = importlib.util.spec_from_file_location("nos_module", data)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # source attributes from loaded .py module
        self.name = getattr(module, "name", self.name)
        self.commands = getattr(module, "commands", self.commands)
        self.initial_prompt = getattr(module, "INITIAL_PROMPT", self.initial_prompt)

    def from_file(self, data: str) -> None:
        """
        Method to load NOS from YAML or Python file

        :param data: OS path string to `.yaml/.yml` or `.py` file with NOS data
        """
        if not self.is_file_ending_correct(data):
            raise ValueError(
                f'Unsupported "{data}" file extension.\
                              Supported: .py, .yml, .yaml'
            )
        if data.endswith((".yaml", ".yml")):
            self.from_yaml(data)
        elif data.endswith(".py"):
            self.from_module(data)

    def is_file_ending_correct(self, data: str) -> None:
        """
        Method to check if file extension is correct and load NOS data.
        Correct types are: .yaml, .yml and .py
        """
        return data.endswith((".yaml", ".yml", ".py"))
