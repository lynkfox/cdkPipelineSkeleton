# How to set up a Local PYTHONPATH

First:

**You never change the code to work in your local - you change your local to work with what the code already has.**

Again - do NOT change the code files so that it works for your local. Instead, you modify your local to mimic the production environment.

## A Primer on PYTHONPATH and the Python Interpreter.

When the Python starts up the interpreter (including when running Pytest, any testing UI, the debugger, and more) it reads the starting file. Imports are at the top because the Interpreter reads from top to bottom. When it finds an Import statement, it attempts to connect the path provided from any starting points it has in the PYTHONPATH environment variable.

When you run these things from inside a Virtual Environment, say for instance a team product repo like this one, the PYTHONPATH variable includes the base point from where the file is running... but this is a bit tricky.

For example, if you navigate to a directory in the terminal, and use `python my_script.py` then starting point for PYTHONPATH and where the Interpreter looks for imports is location of that file.

But if you run that file from a higher directory, something like: `python scripts/important/my_script.py` then the PYTHONPATH assumes where you are running it from is the entry point and looks for imports from there.

If you add additional directories and paths to the PYTHONPATH env variable, then the interpreter *also* looks for imports from there.

## Related to AWS:

This is very important with AWS and Lambdas.

The best practice is to confine a given lambda's code to a single directory, and point CDK at that single directory. This prevents unnecessary files from being deployed to your lambda code. If you are not careful with where you call the source of your lambda code, you will end up with additional unnecessary files in your lambda, creating security risks and possibly making it so you cannot even look at the code in the AWS Console.

However, this means that any given directory will be considered the starting point for a lambda. If your lambda code is contained in `aws_lambda_functions/hello_world` and you point CDK to this point to bundle the code for asset generation, then the Python Interpreter in the AWS Lambda running your code will begin its Imports from that directory.

This is fine in the lambda. But when you try and run this code in Pytest or else-wise in your local, it will not know to begin looking there - especially if you keep your tests in a separate directory (again, so they do not get deployed to your lambda as well)


# Updating your PYTHONPATH variable...

## ...quick and dirty:
The simplest way is to update your PYTHONPATH variable.

`$ export PYTHONPATH="{$PYTHONPATH}:./aws_lambda_functions/hello_world:./aws_lambda_functions/goodbye_for_now`

The issue is that this only lasts in that current Terminal shell - the moment you close that terminal its gone. In addition, if you have many different products in your local, you don't want them overlapping

## ...with VS Code:

This repo comes already set up for the basics, but its kind of clunky if you have a lot of lambdas. It also can be very finicky between locals.

As a basic first step, the `.env` file has a `PYTHONPATH` attribute within it. Adding additional starting points for PYTHONPATH

`PYTHONPATH="${PYTHONPATH}:./aws_lambda_functions/hello_world:./aws_lambda_functions/goodby_for_now"`

Then `.vscode/settings.json` - your local workspace (just this product) settings needs updated.

```json
{
    "python.envFile": "${workspaceFolder}/.env",
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${env.PYTHONPATH}"
    },
    "terminal.integrated.env.osx": {
        "PYTHONPATH": "${env.PYTHONPATH}"
    },
}
```

*Note: This repo is already set up with these*

This unfortunately has a draw back that every time a new directory is added that needs added to the python path this will have to be updated. This causes some issues.
## ...with Pycharm:

*Needs written*


## A more dynamic solution:

If you have a lot of lambdas and are always adding more, manually creating a link to each directory would be a major pain. Instead, you could create a script that does it for you:

```bash
ROOT_PATH="$(find ./aws_lambda_functions -maxdepth 1 -type d -not -path "./" -not -path "./__pycache__" -not -path "./.venv" -not -path "./.git" -not -path "./.vscode" -not -path "./common" | sed '/\/\./d' | tr '\n' ':' | sed 's/:$//')"
# parse the root directory and add all top level folders to the python path
export PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"
```

The above snippet of code does this for each directory inside the `aws_lambda_functions` directory. This is very useful for adding before you run tests through a script - such as in a Codebuild environment.

But it does not help a developers local that much, because its still ephemeral - And will not affect their test UIs or debugger.

A potential solution would be to create a `pre-commit-hook` to automatically update the `.env` file every time a commit is made to your repo. This will ensure that it it always stays up to date.


# A Note on Layers and Common functionalities

*Note: process is the same for libraries that are not native to aws lambda images*

Like any good team, your product likely has a some very common utilities that are used across multiple lambdas. Since you don't want to have duplicates in each lambda directory, then you want to put them in a common location. You can do some tricky stuff with telling the `AssetCode` cdk functionality to grab those files too, but that is rather difficult.

Instead we create a layer.

This product repo uses a `makefile` to accomplish this. It needs to be run before a manual `cdk deploy` and be included in the files that CDK uses to deploy in your teams pipeline. *Note: this repo already has this all set up*

The key thing is that all files to be accessed/imported from a layer for Python need to be in a `python` directory inside a zip. This is because when AWS Lambda loads, it also loads the associated layers, and the `python` directories are considered part of the PYTHONPATH in the AWS Lambda environments already, allowing smooth imports.

This *does* mean that it is simplest to simply put all you common functionalities into the same directory, and import that into your Lambda *as the same import path from your repo's root* - which is counter-intuitive to the above statements about AWS Lambdas and root.
