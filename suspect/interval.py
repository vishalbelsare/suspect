# Copyright 2017 Francesco Ceccon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Numerical interval object."""

from typing import Any, Callable, Generic, SupportsFloat, TypeVar, Union
from functools import wraps
# pylint: disable=no-name-in-module
from suspect.math import (
    almosteq,
    almostgte,
    almostlte,
    inf,
    zero,
    pi,
    down,
    up,
    make_number,
    min_,
    max_,
    exp,
    log,
    sqrt,
    sin,
    cos,
    tan,
    asin,
    acos,
    atan,
)
from suspect.math import RoundMode as RM


# Internal type used for math.
T = TypeVar('T', bound=SupportsFloat)


class _FunctionOnInterval(object):
    def __init__(self, func: Callable[[], 'Interval[T]'], inv_func: Callable[[], 'Interval[T]']):
        self._func = func
        self._inv_func = inv_func

    def __call__(self):
        return self._func()

    @property
    def inverse(self):
        """Return the inverse of this function."""
        return _FunctionOnInterval(self._inv_func, self._func)


def monotonic_increasing(func):
    """Correctly round monotonic increasing function."""
    # pylint: disable=invalid-name, protected-access
    @wraps(func)
    def _wrapper(it):
        inner = func(it)
        return Interval(inner(it._lower, RM.RD), inner(it._upper, RM.RU))
    return _wrapper


def monotonic_decreasing(func):
    """Correctly round monotonic decreasing function."""
    # pylint: disable=invalid-name, protected-access
    @wraps
    def _wrapper(it):
        inner = func(it)
        return Interval(inner(it._upper, RM.RD), inner(it._lower, RM.RU))
    return _wrapper


class Interval(Generic[T]):
    """Numerical interval."""
    def __init__(self, lower: Any, upper: Any) -> None:
        if lower is None:
            lower = -inf
        if upper is None:
            upper = inf

        lower = make_number(lower)
        upper = make_number(upper)

        if lower > upper:
            raise ValueError('lower must be <= upper')

        self._lower: T = lower
        self._upper: T = upper

    @staticmethod
    def zero() -> 'Interval[T]':
        """Return Interval = [0, 0]."""
        return Interval(zero, zero)

    @property
    def lower_bound(self) -> float:
        """Return interval lower bound."""
        return float(self._lower)

    @property
    def upper_bound(self) -> float:
        """Return interval upper bound."""
        return float(self._upper)

    def size(self) -> T:
        """Return interval size."""
        if self._lower == -inf or self._upper == inf:
            return inf
        return self._upper - self._lower

    def is_zero(self) -> bool:
        """Check if the interval is [0, 0]."""
        return almosteq(self._lower, 0) and almosteq(self._upper, 0)

    def is_positive(self) -> bool:
        """Check if the interval [a, b] has a > 0."""
        return self._lower > zero

    def is_negative(self) -> bool:
        """Check if the interval [a, b] has b < 0."""
        return self._upper < zero

    def is_nonpositive(self) -> bool:
        """Check if the interval [a, b] has b <= 0."""
        return almostlte(self._upper, zero)

    def is_nonnegative(self) -> bool:
        """Check if the interval [a, b] has a >= 0."""
        return almostgte(self._lower, zero)

    def inverse(self) -> 'Interval[T]':
        """Return the inverse of self, or 1/self."""
        return Interval(
            down(lambda: 1.0 / self._upper),
            up(lambda: 1.0 / self._lower),
        )

    def intersect(self, other: 'Interval[T]') -> 'Interval[T]':
        """Intersect this interval with another."""
        if not isinstance(other, Interval):
            raise ValueError('intersect with non Interval value')

        new_lower = max(self._lower, other._lower) # pylint: disable=protected-access
        new_upper = min(self._upper, other._upper) # pylint: disable=protected-access

        if new_upper < new_lower:
            return EmptyInterval()
        return Interval(new_lower, new_upper)

    @property
    def negation(self):
        return _FunctionOnInterval(lambda: -self, lambda: -self)

    @property
    def sqrt(self):  # pragma: no cover
        """Return the bound of sqrt(self)"""
        return _FunctionOnInterval(self._sqrt, self._sqr)

    @property
    def exp(self):  # pragma: no cover
        """Return the bound of exp(self)"""
        return _FunctionOnInterval(self._exp, self._log)

    @property
    def log(self):  # pragma: no cover
        """Return the bound of log(self)"""
        return _FunctionOnInterval(self._log, self._exp)

    @property
    def sin(self):
        """Return the bound of sin(self)"""
        return _FunctionOnInterval(self._sin, self._asin)

    @property
    def cos(self):
        """Return the bound of cos(self)"""
        return _FunctionOnInterval(self._cos, self._acos)

    @property
    def tan(self):
        """Return the bound of tan(self)"""
        return _FunctionOnInterval(self._tan, self._atan)

    @property
    def asin(self):
        """Return the bound of asin(self)"""
        return _FunctionOnInterval(self._asin, self._sin)

    @property
    def acos(self):
        """Return the bound of acos(self)"""
        return _FunctionOnInterval(self._acos, self._cos)

    @property
    def atan(self):
        """Return the bound of atan(self)"""
        return _FunctionOnInterval(self._atan, self._tan)

    def __pos__(self):
        return self

    def __neg__(self):
        return Interval(-self._upper, -self._lower)

    def __add__(self, other: Union[SupportsFloat, 'Interval[T]']) -> 'Interval[T]':
        if not isinstance(other, Interval):
            return self + Interval(float(other), float(other))
        # pylint: disable=protected-access
        return Interval(
            down(lambda: self._lower + other._lower),
            up(lambda: self._upper + other._upper),
        )

    def __radd__(self, other: 'Interval[T]') -> 'Interval[T]':
        return self + other

    def __sub__(self, other: 'Interval[T]') -> 'Interval[T]':
        return self + (-other)

    def __rsub__(self, other: 'Interval[T]') -> 'Interval[T]':
        return (-self) + other

    def __mul__(self, other: Union[SupportsFloat, 'Interval[T]']) -> 'Interval[T]':
        if not isinstance(other, Interval):
            return self * Interval(float(other), float(other))
        if self.is_zero() or other.is_zero():
            return self.zero()
        # pylint: disable=protected-access
        sl = self._lower
        su = self._upper
        ol = other._lower
        ou = other._upper
        return Interval(
            down(lambda: min_(sl*ol, sl*ou, su*ol, su*ou)),
            up(lambda: max_(sl*ol, sl*ou, su*ol, su*ou)),
        )

    def __rmul__(self, other: Union[SupportsFloat, 'Interval[T]']) -> 'Interval[T]':
        return self * other

    def __div__(self, other: Union[SupportsFloat, 'Interval[T]']) -> 'Interval[T]':
        if not isinstance(other, Interval):
            return self / Interval(float(other), float(other))
        if 0 in other:
            return Interval(None, None)
        return self * other.inverse()

    __truediv__ = __div__

    def __rdiv__(self, other: Union[SupportsFloat, 'Interval[T]']) -> 'Interval[T]':
        if not isinstance(other, Interval):
            return Interval(float(other), float(other)) / self
        if 0 in self:
            return Interval(None, None)
        return self.inverse() * other

    __rtruediv__ = __rdiv__

    def __eq__(self, other: 'Interval[T]') -> bool:
        if not isinstance(other, Interval):
            return False
        # pylint: disable=protected-access
        return (
            almosteq(self._lower, other._lower) and
            almosteq(self._upper, other._upper)
        )

    def __contains__(self, other: Union['Interval[T]', SupportsFloat]) -> bool:
        # pylint: disable=protected-access
        if isinstance(other, Interval):
            return (
                almostlte(self._lower, other._lower) and
                almostlte(other._upper, self._upper)
            )
        other = float(other)
        return almostlte(self._lower, other) and almostlte(other, self._upper)

    def __repr__(self):
        return '<{} at {}>'.format(str(self), hex(id(self)))

    def __str__(self):
        return 'Interval([{}, {}])'.format(self._lower, self._upper)

    @monotonic_increasing
    def _sqrt(self):
        return sqrt

    def _sqr(self):
        new_lower = down(lambda: self._lower * self._lower)
        new_upper = up(lambda: self._upper * self._upper)
        return Interval(new_lower, new_upper)

    @monotonic_increasing
    def _exp(self):
        return exp

    @monotonic_increasing
    def _log(self):
        return log

    def _sin(self):
        if almostgte(self.size(), 2*pi):
            return Interval(None, None)
        lower = self._lower % (2*pi)
        upper = lower + (self._upper - self._lower)
        new_lower = min_(sin(lower, RM.RD), sin(upper, RM.RD))
        new_upper = max_(sin(lower, RM.RU), sin(upper, RM.RU))
        new = Interval(new_lower, new_upper)
        if 0.5 * pi in new:
            new_upper = 1.0
        if 1.5 * pi in new:
            new_lower = -1.0
        return Interval(new_lower, new_upper)

    def _cos(self):
        if almostgte(self.size(), 2*pi):
            return Interval(None, None)
        # translate by pi/2 and class sin
        pi_2 = pi/2.0
        return (self + pi_2).sin()

    def _tan(self):
        if almostgte(self.size(), pi):
            return Interval(None, None)
        lower = self._lower % pi
        upper = lower  + (self._upper - self._lower)
        new_lower = min_(tan(lower, RM.RD), tan(upper, RM.RD))
        new_upper = max_(tan(lower, RM.RU), tan(upper, RM.RU))

        if almosteq(lower, 0.5 * pi):
            new_lower = None

        if almosteq(upper, 0.5 * pi):
            new_upper = None

        if new_lower is not None and new_upper is not None:
            new = Interval(new_lower, new_upper)
            if 0.5*pi in new or pi in new:
                return Interval(None, None)
        return Interval(new_lower, new_upper)

    @monotonic_increasing
    def _asin(self):
        return asin

    @monotonic_decreasing
    def _acos(self):
        return acos

    @monotonic_increasing
    def _atan(self):
        return atan


class EmptyInterval(Interval):
    """An empty interval."""
    def __init__(self) -> None:
        super().__init__(0, 0)
