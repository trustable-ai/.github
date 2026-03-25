# Trustable Support & FAQ

## What is Trustable?

Trustable is a private vibe-coding platform inspired by Lovable.dev. It provides a complete cloud infrastructure for building applications using AI-assisted development, while keeping your data and code under your control.

## Does it use cloud models?

Trustable uses private AI models that run in the cloud but can also be executed locally. If you have a GPU available, you can run everything entirely on your own machine for full privacy and independence.

## How do I report a bug or request a feature?

Please open an issue on our support repository:

https://github.com/trustable-ai/.github/issues

When reporting a bug, include the following to help us resolve it quickly:

- A clear description of the problem
- Steps to reproduce the issue
- The output of `ops trustable logs` (if applicable)
- Your operating system and version


To view the Trustable application logs, run:

```
ops trustable logs
```

This is useful for diagnosing errors or checking the status of running services.

Log display is continuous, interrupt with control-c.

## How do I update Trustable?

To update Trustable to the latest version, run:

```
ops trustable update
```



We recommend keeping Trustable up to date to benefit from the latest features and bug fixes.

## How do I uninstall Trustable?

To completely remove Trustable from your system, run:

```
ops trustable uninstall
```

This will stop all running services and remove the installed components.
