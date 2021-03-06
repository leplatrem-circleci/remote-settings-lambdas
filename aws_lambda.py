#!/usr/bin/env python
import glob
import importlib
import os
import sys

import sentry_sdk
from decouple import config
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

SENTRY_DSN = config("SENTRY_DSN", default=None)

if SENTRY_DSN:
    # Note! If you don't do `sentry_sdk.init(DSN)` it will still work
    # to do things like calling `sentry_sdk.capture_exception(exception)`
    # It just means it's a noop.
    sentry_sdk.init(SENTRY_DSN, integrations=[AwsLambdaIntegration()])


def help_(**kwargs):
    """Show this help."""

    def white_bold(s):
        return f"\033[1m\x1B[37m{s}\033[0;0m"

    entrypoints = [
        os.path.splitext(os.path.basename(f))[0]
        for f in glob.glob("./commands/[a-z]*.py")
    ]
    commands = [
        getattr(importlib.import_module(f"commands.{entrypoint}"), entrypoint)
        for entrypoint in entrypoints
    ]
    func_listed = "\n - ".join(
        [f"{white_bold(f.__name__)}: {f.__doc__}" for f in commands]
    )
    print(
        f"""
Remote Settings lambdas.

Available commands:

 - {func_listed}
    """
    )


def run(command, event=None, context=None):
    if event is None:
        event = {"server": os.getenv("SERVER", "http://localhost:8888/v1")}
    if context is None:
        context = {"sentry_sdk": sentry_sdk}

    if isinstance(command, (str,)):
        # Import the command module and returns its main function.
        mod = importlib.import_module(f"commands.{command}")
        command = getattr(mod, command)

    # Note! If the sentry_sdk was initialized with
    # the AwsLambdaIntegration integration, it is now ready to automatically
    # capture all and any unexpected exceptions.
    # See https://docs.sentry.io/platforms/python/aws_lambda/
    command(event, context)


def backport_records(*args, **kwargs):
    return run("backport_records", *args, **kwargs)


def blockpages_generator(*args, **kwargs):
    return run("blockpages_generator", *args, **kwargs)


def publish_dafsa(*args, **kwargs):
    return run("publish_dafsa", *args, **kwargs)


def refresh_signature(*args, **kwargs):
    return run("refresh_signature", *args, **kwargs)


def sync_megaphone(*args, **kwargs):
    return run("sync_megaphone", *args, **kwargs)


def main(*args):
    # Run the function specified in CLI arg.
    #
    # $ AUTH=user:pass python aws_lambda.py refresh_signature
    #

    if not args or args[0] in ("help", "--help"):
        help_()
        return
    entrypoint = args[0]
    try:
        command = globals()[entrypoint]
    except KeyError:
        print(f"Unknown function {entrypoint!r}", file=sys.stderr)
        help_()
        return 1
    command()


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
