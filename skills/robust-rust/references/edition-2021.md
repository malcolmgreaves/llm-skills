# Edition 2021 differences

Read this when the crate's `Cargo.toml` sets `edition = "2021"` (or an older
edition). The skill targets edition 2024 on the latest stable toolchain.
Don't change a crate's edition unless the user asks; to migrate, run
`cargo fix --edition` and then set `edition = "2024"`.

| Edition 2024 | In an edition 2021 crate |
| --- | --- |
| A return-position `impl Trait` captures every lifetime in scope: `fn iter(&self) -> impl Iterator<Item = u64>`. Add `+ use<..>` to capture fewer, such as `+ use<>` for an iterator that doesn't borrow `self`. | Lifetimes aren't captured unless the bounds name them. Add `+ '_` or `+ 'a` when the returned value borrows, or the compiler reports E0700 ("hidden type captures lifetime that does not appear in bounds"). `use<..>` works too. |
| Let chains: `if let Some(x) = found && x > limit { .. }`. | Not available ("let chains are only allowed in Rust 2024 or later"). Nest the `if`, or use `match` or `Option::is_some_and`. |
| An `if let` drops the temporaries of its scrutinee before the `else` branch. | The temporaries live through the `else` branch. In `if let Some(v) = cache.borrow().get(k)`, the borrow is still active in `else`, so a `borrow_mut()` there panics, and a `Mutex` guard deadlocks. Bind the looked-up value with `let` before the `if`. |
| Inside an `unsafe fn`, each unsafe operation must be inside an `unsafe {}` block (the `unsafe_op_in_unsafe_fn` lint warns). | Not required. Write the blocks anyway, each with its `// SAFETY:` comment, and add `#![warn(unsafe_op_in_unsafe_fn)]`. |
| `extern` blocks are `unsafe extern`, and `no_mangle` and `export_name` are written `#[unsafe(..)]`. | The same forms work in 2021 with Rust 1.82 or later. Use them. |

The code examples in the other reference files use edition 2024. In a 2021
crate, add `+ '_` to each `impl Iterator` return type that borrows from
`self` or from an argument.

When the crate sets `rust-version`, use only standard-library APIs that are
stable at that version. Clippy's `incompatible_msrv` lint reports each newer
API, for example `split_at_checked` (Rust 1.80) under `rust-version = "1.79"`.
