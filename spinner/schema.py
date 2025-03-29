from __future__ import annotations

import ast
import itertools as it
import math
import os
import re
from functools import cached_property
from typing import Annotated, Any, Literal, Self

import yaml
from jinja2 import Environment, Template, meta
from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import ErrorDetails

from spinner.app import SpinnerApp

# ==============================================================================
# GLOBALS
# ==============================================================================

# Used for aggregating errors. The first element of the outer tuple is a tuple
# representing the location of the error in the config, e.g.
# `applications.name.output.0`, which would be represented as a tuple (applications,
# name, output, 0). The second element of the outer tuple is the error message to be
# displayed to the user.
_LocationMessagePair = tuple[tuple[int | str, ...], str]
#                            ~~~~~~~~~~~~~~~~~~~~~  ~~~
#                                  LOCATION         MSG

# ==============================================================================
# MODELS
# ==============================================================================


class SpinnerMetadata(BaseModel):
    """The metadata section of the config."""

    description: str
    version: str = Field(pattern=r"^v?\d+\.\d+(\.\d+)?$")
    runs: int = Field(gt=0)
    timeout: PositiveFloat | None = Field(default=None, gt=0.0)
    retry: int = Field(default=0, ge=0)

    @field_validator("retry", mode="before")
    def validate_retry(cls, retry: int | bool) -> int:
        if isinstance(retry, bool):
            return 1 if retry else 0
        return retry


class SpinnerCommand(RootModel):
    """A command template to execute an application."""

    root: str

    def __hash__(self) -> int:
        return hash(self.template)

    def template(self, env: Environment | None = None) -> Template:
        if not env:
            env = Environment()
        return env.from_string(self.root)

    def render(self, env: Environment | None = None, **kwargs) -> str:
        return self.template(env).render(**kwargs)

    @cached_property
    def placeholders(self) -> set[str]:
        return meta.find_undeclared_variables(Environment().parse(self.root))

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return repr(self.root)


class SpinnerLambda(RootModel):
    """A Python lambda function to parse the command output."""

    root: str

    @field_validator("root", mode="after")
    def validate(cls, root: str) -> str:
        root = root.strip()
        try:
            module = ast.parse(source=root)
            assert len(module.body) == 1, "only one expression is allowed"
            body = module.body
            assert isinstance(body[0].value, ast.Lambda), "must be a lambda expression"
            value = body[0].value
            assert len(value.args.args) == 1, "lambda must receive a single argument"
        except SyntaxError as e:
            raise ValueError(f"syntax error: {e}") from e
        except AssertionError as e:
            raise ValueError(f"{e}") from e
        return root

    def __call__(self, *args, **kwargs) -> Any:
        return eval(self.root)(*args, **kwargs)


class SpinnerCaptureAll(BaseModel):
    type: Literal["all"]
    name: str
    func: SpinnerLambda = Field(alias="lambda")

    def process(self, input: str) -> tuple[str, Any]:
        capture = None
        return self.name, capture


class SpinnerCaptureMatches(BaseModel):
    type: Literal["matches"]
    name: str
    pattern: re.Pattern
    func: SpinnerLambda = Field(alias="lambda")

    @field_validator("pattern", mode="before")
    def validate_pattern(cls, pattern: str) -> re.Pattern:
        return re.compile(pattern)

    def process(self, input: str) -> tuple[str, Any]:
        capture = None
        for line in input.splitlines():
            if self.pattern.match(line):
                capture = self.func(line)
                break
        return self.name, capture


SpinnerCapture = Annotated[
    SpinnerCaptureAll | SpinnerCaptureMatches, Field(discriminator="type")
]


class SpinnerPlot(BaseModel):
    title: str = Field(default="")
    x_axis: str
    y_axis: str
    group_by: str | list[str] | None = Field(default=None)


class SpinnerApplication(BaseModel):
    command: SpinnerCommand
    capture: list[SpinnerCapture] = Field(default_factory=list)
    plot: list[SpinnerPlot] = Field(default_factory=list)

    def _validate_plot(self, plot: SpinnerPlot) -> tuple[tuple[Any], str]:
        errors = []
        variables = self.variables.copy() | {"time", "name"}
        if plot.x_axis not in variables:
            errors.append((("plot", "x_axis"), f"undefined x-axis {plot.x_axis!r}"))
        if plot.y_axis not in variables:
            errors.append((("plot", "y_axis"), f"undefined y-axis {plot.y_axis!r}"))
        if plot.group_by and plot.group_by not in variables:
            errors.append(
                (("plot", "group_by"), f"undefined group-by {plot.group_by!r}")
            )
        return errors

    @model_validator(mode="after")
    def plot_axes_are_valid(self) -> Self:
        errors = []
        for plot in self.plot:
            errors += self._validate_plot(plot)
        if errors:
            raise ValidationError.from_exception_data(
                title="SpinnerApplication",
                line_errors=[
                    ErrorDetails(
                        type="value_error", loc=loc, ctx={"error": ValueError(msg)}
                    )
                    for loc, msg in errors
                ],
            )
        return self

    @cached_property
    def captures(self) -> set[str]:
        return set(x.name for x in self.capture)

    @cached_property
    def placeholders(self) -> set[str]:
        return self.command.placeholders

    @cached_property
    def variables(self) -> set[str]:
        return self.placeholders | self.captures

    def render(self, environment: Environment | None = None, **parameters) -> str:
        return self.command.render(environment, **parameters)


class SpinnerApplications(RootModel):
    root: dict[str, SpinnerApplication] = Field(default_factory=dict)

    def items(self):
        return self.root.items()

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, key) -> SpinnerApplication | None:
        return self.root.get(key)

    @cached_property
    def variables(self) -> set[str]:
        return set().union(*(x.variables for _, x in self.items()))


class SpinnerBenchmark(RootModel):
    root: dict[str, list[Any]] = Field(default_factory=dict)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, key) -> list[Any] | None:
        return self.root.get(key)

    def items(self):
        return self.root.items()

    @cached_property
    def parameters(self) -> set[str]:
        return set(self.root.keys())

    @property
    def keys(self) -> list[str]:
        return list(self.root.keys())

    @property
    def values(self) -> list[str]:
        return list(self.root.values())

    @cached_property
    def num_jobs(self) -> int:
        return math.prod(len(x) for x in self.root.values())

    def sweep_parameters(
        self, extra: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        keys = self.keys
        values = self.values
        if extra is not None:
            keys.extend(extra.keys())
            values.extend(extra.values())

        return list(dict(zip(keys, x)) for x in it.product(*values))


class SpinnerBenchmarks(RootModel):
    root: dict[str, SpinnerBenchmark] = Field(default_factory=dict)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, key) -> SpinnerApplication | None:
        return self.root.get(key)

    def __len__(self) -> int:
        return len(self.root)

    @cached_property
    def parameters(self) -> set[str]:
        params = set()
        for _, bench in self.items():
            params |= bench.parameters
        return params

    @cached_property
    def num_jobs(self) -> int:
        return sum(x.num_jobs for x in self.root.values())

    def names(self) -> list[str]:
        return list(self.root.keys())

    def items(self):
        return self.root.items()


class SpinnerConfig(BaseModel):
    metadata: SpinnerMetadata
    applications: SpinnerApplications = Field(default_factory=dict)
    benchmarks: SpinnerBenchmarks = Field(default_factory=dict)

    @staticmethod
    def from_stream(string: str) -> Self:
        return SpinnerConfig.from_data(yaml.safe_load(string))

    @staticmethod
    def from_data(data: dict[str, Any]) -> Self:
        return SpinnerConfig(**data)

    def validate_benchmark_keys(self) -> _LocationMessagePair:
        errors = []

        benchmarks = set(self.benchmarks)
        applications = set(self.applications)

        if difference := benchmarks - applications:
            for benchmark in difference:
                errors.append(
                    (("benchmarks", benchmark), f"benchmark {benchmark!r} is undefined")
                )

        return errors

    def validate_application_placeholders(self) -> _LocationMessagePair:
        errors = []

        for name, application in self.applications.items():
            placeholders = application.command.placeholders
            if name not in self.benchmarks:
                # TODO: Issue a warning when the application has no corresponding
                # benchmark.
                continue

            # Which placeholders that are *not* in the benchmark parameters
            if difference := placeholders - self.benchmarks[name].parameters:
                app = SpinnerApp.get()
                for var in difference:
                    app.info(f"Variable {var!r} not in benchmark parameters.")

        return errors

    @model_validator(mode="after")
    def validate(self) -> Self:
        errors = []
        errors += self.validate_benchmark_keys()
        errors += self.validate_application_placeholders()

        if errors:
            # Create a `ValidationError` that aggregates errors from all validators
            raise ValidationError.from_exception_data(
                title="Spinner Config",
                line_errors=[
                    ErrorDetails(
                        type="value_error", loc=loc, ctx={"error": ValueError(msg)}
                    )
                    for loc, msg in errors
                ],
            )

        return self

    @cached_property
    def num_jobs(self) -> int:
        return self.metadata.runs * self.benchmarks.num_jobs
