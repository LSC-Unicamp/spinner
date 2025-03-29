import re

import click


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
        return {key: value for key, value in pairs}
