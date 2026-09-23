# Before-and-after examples

Each pair shows a typical draft and a rewrite that follows the skill. The
rewrites are shorter, literal, and in present tense, and they name who does
what. Use them as models, not as templates to fill in.

## Contents

- [Chat summary after a task](#chat-summary-after-a-task)
- [Plan](#plan)
- [Explanation of a bug](#explanation-of-a-bug)
- [Commit message](#commit-message)
- [Pull request description](#pull-request-description)
- [README section](#readme-section)
- [Docstring](#docstring)
- [Inline comments](#inline-comments)
- [Error message](#error-message)

## Chat summary after a task

Before:

<!-- style-lint: off -->
> Great news! I've successfully wired up the new retry logic and all tests are
> green. 🎉 Here's what I did:
>
> - **Refactored** the `HttpClient` to leverage a robust exponential backoff
>   strategy under the hood
> - **Added** comprehensive test coverage for the happy path and edge cases
> - **Cleaned up** some cruft in `utils.py` while I was in there
>
> Note that the backoff is load-bearing for the upload path, so it's worth
> keeping an eye on. Let me know if you'd like me to tweak anything!
<!-- style-lint: on -->

After:

> The retry logic is in place and the tests pass (42 passed, 0 failed).
>
> I changed three files:
>
> - `http_client.py`: `HttpClient.send` retries up to 3 times with
>   exponential backoff (1 s, 2 s, 4 s). Only `ConnectionError` and HTTP
>   `503` responses trigger a retry.
> - `test_http_client.py`: tests for a successful send, a send that succeeds
>   on the third try, and a send that fails after 3 retries.
> - `utils.py`: removed the unused `format_bytes` function.
>
> The upload path calls `HttpClient.send` for every chunk, so the retry limit
> also bounds how long an upload can take: 3 retries for each chunk, 7 s
> maximum for each chunk.

What changed: the result comes first, with numbers. Each bullet says what the
code does. *Wired up*, *leverage*, *robust*, *under the hood*, *happy path*,
*cruft*, *load-bearing*, *keep an eye on*, and *tweak* are gone, and so are
the emoji, the exclamation points, and the bold lead-ins.

## Plan

Before:

<!-- style-lint: off -->
> ## Plan
>
> 1. **Investigate** – dig into how the current auth flow works and where the
>    seams are
> 2. **Refactor** – carve out a clean `TokenStore` abstraction that will act
>    as the single source of truth for tokens
> 3. **Migrate** – thread the new store through the request pipeline
> 4. **Verify** – sanity-check with the existing test suite and add coverage
>    for the gotchas we uncover along the way
<!-- style-lint: on -->

After:

> Plan:
>
> 1. Read `auth/session.py` and `auth/middleware.py` to find every place that
>    reads or writes a token. Expected: 4 call sites.
> 2. Add a `TokenStore` class in `auth/token_store.py` with `get`, `set`, and
>    `delete` methods. All token reads and writes go through this class.
> 3. Change the 4 call sites to use `TokenStore`. Remove the module-level
>    `_tokens` dict.
> 4. Run the existing tests. Add tests for an expired token and for a token
>    that is deleted while a request is in flight.

What changed: each step names files, classes, and counts. *Seams*, *carve
out*, *clean*, *single source of truth*, *thread through*, *sanity-check*, and
*gotchas* are replaced by the facts that they stood for. The en dashes and
bold labels are gone.

## Explanation of a bug

Before:

<!-- style-lint: off -->
> So here's the thing: the parser basically chokes when it sees a trailing
> comma, because the tokenizer gets confused and thinks the list is still
> open. It's a classic footgun. The fix is pretty straightforward – we just
> need to teach the tokenizer to be a bit more forgiving.
<!-- style-lint: on -->

After:

> The parser fails on a trailing comma. The tokenizer treats the comma as the
> start of another element, so it never emits the end-of-list token and the
> parser reports an unexpected end of input.
>
> The fix is in `tokenizer.py`: when the tokenizer reads a comma followed by
> `]`, it emits the end-of-list token instead of an element token.

## Commit message

Before:

<!-- style-lint: off -->
> Fix flaky tests and clean things up!
>
> This PR simply bumps the timeout and tweaks a couple of things in the test
> harness so the integration tests stop being janky. Also snuck in a small
> refactor of the logger while I was in there.
<!-- style-lint: on -->

After:

> fix(tests): wait for the server to start before running integration tests
>
> The integration tests sent their first request 100 ms after starting the
> server. On a loaded CI runner the server takes up to 800 ms to bind the
> port, so the first request failed with a connection error.
>
> The test harness now polls the health endpoint until it returns 200, with a
> 5 s limit, before the first test runs.
>
> This commit also renames `log_util.py` to `logging_setup.py`. No behavior
> changes in that file.

What changed: the subject line states the change in the project's commit
format. The body says what the problem was, why it happened, and what the
code does now. *Flaky*, *clean things up*, *simply*, *bumps*, *tweaks*,
*janky*, and *snuck in* are gone.

## Pull request description

Before:

<!-- style-lint: off -->
> ## 🚀 Overview
>
> This PR is a wedge for the bigger storage migration. It lays the groundwork
> by introducing a shiny new `BlobStore` interface that future PRs will build
> on. Nothing user-facing changes yet!
>
> ## ✅ Testing
>
> Ran the full suite locally and everything's green. Should be safe to merge.
<!-- style-lint: on -->

After:

> This change adds the `BlobStore` interface and a `LocalBlobStore`
> implementation. Nothing calls them yet. It's the first of three changes for
> the storage migration; the next change switches `UploadService` to
> `BlobStore`, and the last removes `LegacyStorage`.
>
> Files:
>
> - `storage/blob_store.py`: the `BlobStore` interface (`put`, `get`,
>   `delete`, `list`).
> - `storage/local_blob_store.py`: an implementation backed by a directory on
>   local disk.
> - `tests/test_local_blob_store.py`: tests for each method, including `get`
>   on a missing key.
>
> Testing: `pytest tests/` passes locally (118 passed). No behavior changes
> for users.

## README section

Before:

<!-- style-lint: off -->
> ## Getting Started
>
> Getting up and running is super easy! Simply install the package via pip and
> you're good to go:
>
> ```
> pip install fastcache
> ```
>
> Under the hood, fastcache leverages an LRU eviction strategy to ensure
> blazing-fast lookups. Just wrap any function and let the magic happen:
>
> ```python
> @cached
> def expensive(x): ...
> ```
>
> Note: the default cache size is 128, but you can tweak this as needed.
<!-- style-lint: on -->

After:

> ## Install fastcache
>
> Install the package with pip:
>
> ```
> pip install fastcache
> ```
>
> ## Cache a function
>
> To cache a function's return values, add the `@cached` decorator:
>
> ```python
> @cached
> def expensive(x): ...
> ```
>
> The cache stores up to 128 results and evicts the least recently used result
> when it's full. To change the limit, pass `maxsize`: `@cached(maxsize=1024)`.

What changed: task headings start with a verb. The claims (*super easy*,
*blazing-fast*, *magic*) are replaced by what the cache does and the numbers
that matter. The note became a sentence.

## Docstring

Before:

<!-- style-lint: off -->
```python
def fetch_user(user_id, include_deleted=False):
    """
    This function will fetch a user from the DB. It handles the case where the
    user might have been soft-deleted (e.g. via the admin panel) and should
    gracefully return None if the user isn't found.

    :param user_id: the user's id
    :param include_deleted: whether or not to include deleted users
    :return: the user
    """
```
<!-- style-lint: on -->

After:

```python
def fetch_user(user_id, include_deleted=False):
    """Gets a user by ID.

    Args:
        user_id: The ID of the user to get.
        include_deleted: If true, returns the user even if the user is marked
            as deleted. If false, treats a deleted user as not found.

    Returns:
        The `User` with the given ID, or `None` if no user matches.

    Raises:
        DatabaseError: Thrown when the database connection fails.
    """
```

What changed: the first sentence is short, in third person, and doesn't
repeat the function name. *Will*, *handles*, *might*, *e.g.*, *should*, and
*gracefully* are gone. The boolean parameter states what happens for each
value. The return value states both outcomes.

## Inline comments

Before:

<!-- style-lint: off -->
```python
# HACK: the API is weird and sometimes gives us back a string instead of an
# int here, so we massage it. Should probably fix upstream someday.
count = int(raw_count)

# sanity check
assert count >= 0

# fire off the request and let the retry logic do its thing
client.send(request)
```
<!-- style-lint: on -->

After:

```python
# The /stats endpoint returns `count` as a string for accounts created before
# 2021 (see issue #412). Convert it so both cases are handled the same way.
count = int(raw_count)

# The endpoint never returns a negative count. A negative value means the
# response was parsed incorrectly.
assert count >= 0

# `send` retries up to 3 times on ConnectionError.
client.send(request)
```

What changed: each comment states a fact about the code or the data, with a
reference where one exists. *HACK*, *weird*, *massage*, *should probably*,
*someday*, *sanity check*, *fire off*, and *do its thing* are gone.

## Error message

Before:

<!-- style-lint: off -->
> Oops! Something went wrong while trying to process your request. Please
> make sure the config is valid and try again!
<!-- style-lint: on -->

After:

> Can't read `config.yaml`: line 12 is missing a value for `timeout`. Add a
> value in seconds, such as `timeout: 30`.

What changed: the message says what failed, where, and what to do. No
exclamation points, no *please*, no *config* as a word.
