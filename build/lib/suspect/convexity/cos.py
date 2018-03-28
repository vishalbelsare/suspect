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

from suspect.math.arbitrary_precision import pi
from suspect.convexity.convexity import Convexity
from suspect.bound import ArbitraryPrecisionBound


def cos_convexity(expr, ctx):
    arg = expr.children[0]
    bound = ctx.bound[arg]
    cvx = ctx.convexity[arg]

    if bound.size() > pi:
        return Convexity.Unknown

    cos_bound = bound.cos()
    if cos_bound.lower_bound * cos_bound.upper_bound < 0:
        return Convexity.Unknown

    sin_bound = bound.sin()

    if cos_bound.is_nonnegative():
        if cvx.is_linear():
            return Convexity.Concave
        if cvx.is_convex() and sin_bound.is_nonpositive():
            return Convexity.Concave
        if cvx.is_concave() and sin_bound.is_nonnegative():
            return Convexity.Concave
    elif cos_bound.is_nonpositive():
        if cvx.is_linear():
            return Convexity.Convex
        if cvx.is_concave() and sin_bound.is_nonpositive():
            return Convexity.Convex
        if cvx.is_convex() and sin_bound.is_nonnegative():
            return Convexity.Convex

    return Convexity.Unknown


def acos_convexity(expr, ctx):
    arg = expr.children[0]
    bound = ctx.bound[arg]
    cvx = ctx.convexity[arg]

    convex_domain = ArbitraryPrecisionBound(-1, 0)
    if bound in convex_domain and cvx.is_concave():
        return Convexity.Convex

    concave_domain = ArbitraryPrecisionBound(0, 1)
    if bound in concave_domain and cvx.is_convex():
        return Convexity.Concave

    return Convexity.Unknown