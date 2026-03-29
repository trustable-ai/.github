# Trustable Support & FAQ

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

## What is Trustable?

Trustable is a private vibe-coding platform inspired by Lovable.dev. It provides a complete cloud infrastructure for building applications using AI-assisted development, while keeping your data and code under your control.

## Does it use cloud models?

Trustable uses private AI models that run in the cloud but can also be executed locally. If you have a GPU available, you can run everything entirely on your own machine for full privacy and independence.

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


## I cannot ensure prerequisites

If you get errors in prerequisites (tipically on windows) you will get something like this:

```
ops trustable setup
ensuring prerequisite 7zz 2407
error in prereq 7zz: failed to download 7zz version 2407
ensuring prerequisite rg 14.1.0
error in prereq rg: failed to download rg version 14.1.0
ensuring prerequisite zip 3.0-1
error in prereq zip: failed to download zip version 3.0-1
ensuring prerequisite coreutils 0.0.27
error in prereq coreutils: failed to download coreutils version 0.0.27
ensuring prerequisite bun 1.2.5
error in prereq bun: failed to download bun version 1.2.5
ensuring prerequisite k3sup 0.13.6
error in prereq k3sup: failed to download k3sup version 0.13.6
ensuring prerequisite uv 0.7.19
error in prereq uv: failed to download uv version 0.7.19
ensuring prerequisite helm 3.18.0
error in prereq helm: failed to download helm version 3.18.0
ensuring prerequisite kubectl 1.33.1
error in prereq kubectl: failed to download kubectl version 1.33.1
ensuring prerequisite kind 0.30.0
error in prereq kind: failed to download kind version 0.30.0
ensuring prerequisite yq 4.47.1
error in prereq yq: failed to download yq version 4.47.1
"coreutils": executable file not found in $PATH
ops: Failed to run task "setup": exit status 127
error: ops: Failed to run task "setup": exit status 127
```

Verify the problem trying a direct download:

```
curl.exe -o kubectl.exe -L https://dl.k8s.io/release/v1.33.1/bin/windows/amd64/kubectl.exe
```

You need to disable (temporarily) any antivirus that will block downloads of executables.



