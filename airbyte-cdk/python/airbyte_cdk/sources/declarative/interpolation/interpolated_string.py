#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from typing import Any, Mapping, Optional, Union

from airbyte_cdk.sources.declarative.interpolation.jinja import JinjaInterpolation


class InterpolatedString:
    """Wrapper around a raw string to be interpolated with the Jinja2 templating engine"""

    def __init__(self, string: str, default: Optional[str] = None, options=None):
        """
        :param string: string to evaluate
        :param default: Default value to return if the evaluation returns an empty string
        :param options: Interpolation parameters propagated by parent component
        """
        self._string = string
        self._default = default or string
        self._interpolation = JinjaInterpolation()
        self._options = options or {}

    def eval(self, config, **kwargs):
        return self._interpolation.eval(self._string, config, self._default, options=self._options, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, InterpolatedString):
            return False
        return self._string == other._string and self._default == other._default

    @classmethod
    def create(
        cls,
        string_or_interpolated: Union["InterpolatedString", str],
        /,
        options: Mapping[str, Any],
        default=None,
    ):
        """
        Helper function to obtain an InterpolatedString from either a raw string or an InterpolatedString.
        :param string_or_interpolated: either a raw string or an InterpolatedString.
        :param options: options parameters propagated from parent component
        :return: InterpolatedString representing the input string.
        """
        if isinstance(string_or_interpolated, str):
            return InterpolatedString(string_or_interpolated, default=default, options=options)
        else:
            return string_or_interpolated
