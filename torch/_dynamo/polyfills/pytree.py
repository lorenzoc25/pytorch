"""
Python polyfills for torch.utils.pytree
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Literal, TYPE_CHECKING

import torch.utils._pytree as python_pytree

from ..decorators import substitute_in_graph


if TYPE_CHECKING:
    from torch.utils._cxx_pytree import PyTree


__all__: list[str] = []


if python_pytree._cxx_pytree_exists:
    import optree

    import torch.utils._cxx_pytree as cxx_pytree

    @substitute_in_graph(
        optree._C.is_dict_insertion_ordered,
        can_constant_fold_through=True,
    )
    def always_true(*args: Any, **kwargs: Any) -> Literal[True]:
        # In namespace 'torch', the dictionary is always traversed in insertion order.
        return True

    @substitute_in_graph(cxx_pytree.tree_iter)
    def tree_iter(
        tree: PyTree,
        is_leaf: Callable[[PyTree], bool] | None = None,
    ) -> Iterable[Any]:
        stack = [tree]
        while stack:
            curr = stack.pop()
            if curr is None or (is_leaf is not None and is_leaf(curr)):
                yield curr
                continue
            if optree.register_pytree_node.get(type(curr), namespace="torch") is None:  # type: ignore[attr-defined]
                yield curr
                continue

            (
                children,
                metadata,
                entries,
                unflatten_func,
            ) = optree.tree_flatten_one_level(
                curr,
                is_leaf=is_leaf,
                none_is_leaf=True,
                namespace="torch",
            )
            stack.extend(reversed(children))

    __all__ += ["tree_iter"]

    @substitute_in_graph(cxx_pytree.tree_leaves, can_constant_fold_through=True)
    def tree_leaves(
        tree: PyTree,
        is_leaf: Callable[[PyTree], bool] | None = None,
    ) -> list[Any]:
        return list(tree_iter(tree, is_leaf=is_leaf))

    __all__ += ["tree_leaves"]
