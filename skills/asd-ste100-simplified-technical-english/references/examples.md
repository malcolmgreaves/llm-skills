# Examples

Each example gives a text that does not obey STE, and then the same text in
STE. Each STE text keeps all the facts of the first text. If the first text is
not sure about a fact, the STE text is also not sure. Code, identifiers, and the text of messages in the code do not
change.

## Contents

- [Reply after a change to the code](#reply-after-a-change-to-the-code)
- [Status report with a cause that is not sure](#status-report-with-a-cause-that-is-not-sure)
- [Explanation](#explanation)
- [Plan](#plan)
- [Runbook procedure with a caution](#runbook-procedure-with-a-caution)
- [Commit message](#commit-message)
- [Pull request description](#pull-request-description)
- [README section](#readme-section)
- [Docstring and comments](#docstring-and-comments)
- [Error message](#error-message)
- [Review comment](#review-comment)

## Reply after a change to the code

<!-- ste-lint: off -->
Before:

> Great news — I've fixed the flaky test! The issue was that `test_upload` was
> relying on the system clock, so it would sometimes fail when the minute
> rolled over. I refactored it to use a frozen clock via `freezegun`, and now
> it passes consistently. You might also want to run the full suite before
> merging, since I only ran the tests in `tests/storage/`.
<!-- ste-lint: on -->

STE:

> The test `test_upload` passes. I ran it 50 times, and it did not fail.
>
> The cause of the problem was the system clock. The test read the clock two
> times. If the minute changed between the first time and the second time,
> the test failed. After the change, the test sets the clock to a specified
> time with `freezegun`.
>
> I ran only the tests in `tests/storage/`. Before you merge, run all the
> tests with `pytest`.

The rewrite gives the result first. It gives the data for the result (50
runs), the cause, and the change. The last paragraph tells the user which
tests did not run, and gives the step for the user as a command.

## Status report with a cause that is not sure

<!-- ste-lint: off -->
Before:

> The deploy is still failing. It's probably a DNS issue since the health
> checks time out, but I haven't been able to confirm that yet. I'm going to
> dig into the resolver logs next.
<!-- ste-lint: on -->

STE:

> The deployment continues to fail. The health checks stop after the timeout
> of 30 seconds.
>
> It is possible that DNS is the cause. The health checks use the host name of
> the service, and the DNS resolver recorded 12 errors in the last hour. I did
> not examine the logs of the resolver. Thus, I do not know the cause at this
> time.
>
> I will examine the logs of the resolver as the next step.

The first text is not sure about the cause, and the STE text is also not sure.
*Probably* has no STE word. Thus, the rewrite gives the data and the step that
did not occur.

## Explanation

<!-- ste-lint: off -->
Before:

> Rebasing basically rewrites your branch's history so it looks like you
> started from the latest main. It's super handy for keeping a clean, linear
> history, but be careful: never rebase commits you've already pushed, since
> that'll mess up everyone else's copies.
<!-- ste-lint: on -->

STE:

> The `git rebase` command moves the commits of your branch to the end of a
> different branch, usually `main`. Git makes a new copy of each commit. As a
> result, the history of your branch is one straight line.
>
> CAUTION: Do not rebase commits that you pushed to a branch that other
> persons use. A rebase changes the IDs of the commits. As a result, the
> copies of the other persons do not agree with your branch.

The first paragraph is descriptive. The risk is in a safety instruction that
starts with a command and then tells the result.

## Plan

<!-- ste-lint: off -->
Before:

> Here's my plan:
>
> 1. First, I'll add a `retry` decorator to handle transient failures.
> 2. Then wire it up to the HTTP client so that all outgoing requests get
>    retried.
> 3. Finally, add tests covering the backoff logic.
<!-- ste-lint: on -->

STE:

> The plan has three steps:
>
> 1. Add a `retry` decorator. The decorator calls the function again after a
>    timeout or a `503` response.
> 2. Apply the decorator to all requests that the HTTP client sends.
> 3. Write tests for the backoff (the wait time before each retry).

Each step starts with a command. The rewrite replaces *transient failures*
with the two errors that it refers to. It also tells the meaning of *backoff*.

## Runbook procedure with a caution

<!-- ste-lint: off -->
Before:

> ### Rotating the database password
>
> To rotate the password, first generate a new one in Vault, then update the
> `DB_PASSWORD` secret and restart the `billing` pods. Note: make sure you
> revoke the old password afterwards, otherwise it remains valid. Be careful
> — restarting the pods will drop active connections.
<!-- ste-lint: on -->

STE:

> ### Change the database password
>
> Do this procedure each 90 days.
>
> 1. Make a new password in Vault:
>
>    ```bash
>    vault write -f database/rotate-role/billing
>    ```
>
> 2. Write the new password in the `DB_PASSWORD` secret.
> 3. CAUTION: Before you restart the pods, make sure that the traffic is low.
>    The restart stops all connections to the database, and requests that are
>    in progress fail.
>
>    Restart the `billing` pods:
>
>    ```bash
>    kubectl rollout restart deployment/billing
>    ```
>
> 4. Make sure that all `billing` pods show `Running`.
> 5. Cancel the previous password in Vault.
>
> NOTE: The previous password continues to operate until you cancel it.

The heading is a command. Each step has one instruction. The caution comes
before the step that has the risk. The note gives information only. The
command to cancel the password is a step, not a note.

## Commit message

<!-- ste-lint: off -->
Before:

```text
fix: handle empty input in parser

Previously the parser would crash with an IndexError when given an empty
string. This commit adds a guard clause that returns an empty AST instead,
and adds a regression test.
```
<!-- ste-lint: on -->

STE:

```text
fix(parser): return an empty AST for empty input

For an empty string, the parser raised an IndexError. After this change, the
parser returns an empty AST. A new regression test examines this condition.
```

The subject line obeys the style of the project (Conventional Commits) and
starts with a command. The body is descriptive.

## Pull request description

<!-- ste-lint: off -->
Before:

> ## Summary
>
> This PR migrates the user table to the new schema. It's a pretty big
> change, so please review carefully!
>
> ## Testing
>
> Run the migration locally and verify that everything works.
<!-- ste-lint: on -->

STE:

> ## Summary
>
> This pull request moves the `users` table to schema version 2. The
> migration adds the column `email_verified` and removes the column
> `legacy_id`.
>
> ## Test procedure
>
> 1. CAUTION: Before you do this step, make a backup of your local database.
>    The migration removes the column `legacy_id`, and you cannot get its data
>    again.
>
>    Run the migration with `make migrate`.
>
> 2. Run the tests with `make test`. All tests must pass.
> 3. Make sure that the `users` table has the column `email_verified`.

The rewrite gives the facts that make the change large. The test procedure
tells the reader the result that must occur.

## README section

<!-- ste-lint: off -->
Before:

> ## Configuration
>
> The tool can be configured via a `config.toml` file, which should live in
> the project root. If it's not present, sensible defaults are used. You can
> override any setting with an env var, e.g. `APP_TIMEOUT=30`.
<!-- ste-lint: on -->

STE:

> ## Configuration file
>
> The tool reads its settings from the file `config.toml` in the root
> directory of the project. If there is no `config.toml` file, the tool uses
> its default settings.
>
> An environment variable can override a setting. The name of the variable
> starts with `APP_`. The name of the setting, in uppercase letters, comes
> after it. For example, `APP_TIMEOUT=30` sets `timeout` to 30 seconds.
>
> ## Change a setting
>
> 1. Open `config.toml`.
> 2. Set the value, for example `timeout = 60`.
> 3. Save the file. The tool reads the new value when it starts.

The descriptive section has a noun heading. The procedural section has a
command heading and numbered steps.

## Docstring and comments

<!-- ste-lint: off -->
Before:

```python
def retry(fn, attempts=3):
    """Decorator that retries fn on failure.

    Uses exponential backoff so we don't hammer the server. Should only be used
    for idempotent calls!
    """
    # loop until we either succeed or run out of attempts
    for i in range(attempts):
        try:
            return fn()
        except TransientError:
            time.sleep(2 ** i)  # back off exponentially
    raise RetryError(f"gave up after {attempts} attempts")
```
<!-- ste-lint: on -->

STE:

```python
def retry(fn, attempts=3):
    """Call `fn` again after a `TransientError`, a maximum of `attempts` times.

    The wait time before each retry is two times the previous wait time
    (exponential backoff). The backoff decreases the load on the server. This function is
    only for idempotent calls. For a different call, a retry can do the
    operation two times.
    """
    for i in range(attempts):
        try:
            return fn()
        except TransientError:
            time.sleep(2 ** i)  # The wait times are 1 s, 2 s, and 4 s.
    raise RetryError(f"gave up after {attempts} attempts")
```

The first line of the docstring is a command, because Python uses that style.
The other sentences of the docstring are descriptive. It tells the risk as a fact, not as
a command. The comment on the loop told only the function of the code, thus
the rewrite removes it. The text of the `RetryError` message does not change,
because it is a message in the code.

## Error message

<!-- ste-lint: off -->
Before:

```text
Oops! Couldn't find config file — maybe you forgot to run init?
```
<!-- ste-lint: on -->

STE:

```text
The file config.yaml is missing. To make it, run "app init".
```

The message tells the problem first. Then it gives the command that corrects
the problem.

## Review comment

<!-- ste-lint: off -->
Before:

> nit: this could probably be simplified with a dict comprehension, but LGTM
> otherwise!
<!-- ste-lint: on -->

STE:

> Small change, optional: A dictionary comprehension can replace the loop in
> lines 12 to 18. All other parts of the change are correct, and I give my
> approval.
