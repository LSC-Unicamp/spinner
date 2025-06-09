import re

import click
import yaml


class ExtraArgs(click.ParamType):
    name = "extra_args"
    validate = re.compile(r"^(\w+)=([^;]+)(?:;(\w+)=([^;]+))*;?$")
    parse = re.compile(r"(\w+)=([^;]+)")

    def convert(self, value, param, ctx):
        if not isinstance(value, str):
            raise ValueError("Expected a string")

        if not self.validate.match(value):
            raise ValueError(
                "Expected a list of key=value pairs separated by semicolon"
            )

        pairs = self.parse.findall(value)
        result = {}
        for key, val in pairs:
            try:
                result[key] = yaml.safe_load(val)
            except Exception:
                result[key] = val
        return result
