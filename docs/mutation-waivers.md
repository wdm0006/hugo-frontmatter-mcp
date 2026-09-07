# Mutation waiver register

The mutmut 3.7.0 campaign runs over `hugo_frontmatter_mcp.py`
(`[tool.mutmut] source_paths`). As of this register the campaign produces
**201 mutants: 189 killed by the test suite (94.0%), 12 waived below**.

Every survivor is either killed by a named test or waived here with a
classification. Re-run with `uv run mutmut run`; a waiver is only valid for
the exact mutant described.

## Waived mutants

| Mutant | Location | Classification | Justification |
|---|---|---|---|
| `_save_post__mutmut_10` | `frontmatter.dump(post, file_path_str, sort_keys=False)` → `sort_keys=None` | **equivalent** | PyYAML treats an explicit `sort_keys=None` as falsy, so the written bytes are identical. Verified empirically: dumping a post with non-alphabetical keys under `sort_keys=False` and `sort_keys=None` produces byte-identical files. No test can distinguish the two behaviors because there is none. |
| `_modify_list_field__mutmut_22`, `_modify_list_field__mutmut_23` | `made_change = False` → `None` / `True` | **inert** | `made_change` is provably write-only before any read: the `add`/`remove` branches either return early (duplicate / not-found / invalid action) or set `made_change = True` immediately after mutating the list. The only read, `if not made_change:`, is therefore unreachable dead code (see next entry), so the initialization value is unobservable. |
| `_modify_list_field__mutmut_58`–`_modify_list_field__mutmut_66` (9 mutants) | the `if not made_change: return {"message": "No effective change made.", ...}` safeguard | **inert** | Unreachable defensive branch. `action` is validated by the surrounding `if/elif/else` (any value other than `add`/`remove` returns the "Invalid action" error), and both handled branches either return early or set `made_change = True`. No input can reach the safeguard, so mutants of its dict keys/message cannot be observed by any test. |

## Not waived

All other survivors from the initial campaign (109 after the first full run)
were killed by committed tests, principally the result-contract suite in
`tests/test_frontmatter_api.py` (`TestLoadPostErrorContract`,
`TestSavePostErrorContract`, `TestModifyListFieldContract`,
`TestSetSpecificFieldContract`, `TestModifyListFieldPostNoneGuard`), which
pins every error/success dict's keys, message text, and interpolated
exception content.
