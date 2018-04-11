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

from suspect.math import almosteq, almostlte, almostgte
from suspect.convexity.convexity import Convexity


def _numeric_exponent_pow_convexity(base, exponent, ctx):
    is_integer = almosteq(exponent, int(exponent))
    is_even = almosteq(exponent % 2, 0)

    cvx = ctx.convexity[base]
    bound_base = ctx.bound[base]

    if almosteq(exponent, 0):
        return Convexity.Linear
    elif almosteq(exponent, 1):
        return cvx
    elif is_integer and is_even and exponent > 0:
        if cvx.is_linear():
            return Convexity.Convex
        elif cvx.is_convex() and bound_base.is_nonnegative():
            return Convexity.Convex
        elif cvx.is_concave() and bound_base.is_nonpositive():
            return Convexity.Convex

    elif is_integer and is_even and almostlte(exponent, 0):
        if cvx.is_convex() and bound_base.is_nonpositive():
            return Convexity.Convex
        elif cvx.is_concave() and bound_base.is_nonnegative():
            return Convexity.Convex
        elif cvx.is_convex() and bound_base.is_nonnegative():
            return Convexity.Concave
        elif cvx.is_concave() and bound_base.is_nonpositive():
            return Convexity.Concave

    elif is_integer and exponent > 0:  # odd
        if almosteq(exponent, 1):
            return cvx
        elif cvx.is_convex() and bound_base.is_nonnegative():
            return Convexity.Convex
        elif cvx.is_concave() and bound_base.is_nonpositive():
            return Convexity.Concave

    elif is_integer and almostlte(exponent, 0):  # odd negative
        if cvx.is_concave() and bound_base.is_nonnegative():
            return Convexity.Convex
        elif cvx.is_convex() and bound_base.is_nonpositive():
            return Convexity.Concave

    else:
        # not integral
        if bound_base.is_nonnegative():
            if cvx.is_convex() and exponent > 1:
                return Convexity.Convex
            elif cvx.is_concave() and exponent < 0:
                return Convexity.Convex
            elif cvx.is_concave() and 0 < exponent < 1:
                return Convexity.Concave
            elif cvx.is_convex() and exponent < 0:
                return Convexity.Concave

    return Convexity.Unknown


def pow_convexity(expr, ctx):
    assert len(expr.children) == 2
    base, exponent = expr.children

    mono_base = ctx.monotonicity[base]
    mono_exponent = ctx.monotonicity[exponent]

    if mono_exponent.is_constant():
        return _numeric_exponent_pow_convexity(
            base,
            exponent.value,
            ctx,
        )
    elif mono_base.is_constant():
        base = base.value
        cvx = ctx.convexity[exponent]
        if 0 < base < 1:
            if cvx.is_concave():
                return Convexity.Convex

        elif almostgte(base, 1):
            if cvx.is_convex():
                return Convexity.Convex
            else:
                return Convexity.Unknown

    return Convexity.Unknown