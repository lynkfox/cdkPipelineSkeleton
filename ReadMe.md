# Devops Style Pipeline and Tools framework

This repo contains a somewhat generic pipeline and utilities that can be used to enhance your teams CICD and devops procedures.

This repo is organized as a single unit, and can be dumped into other projects with some tweaking.
### **DISCLIAMER**

This is a *Skeleton* or *Framework* for a product CICD pipeline and associated tools. It may not work as is for your team. It may not work as is at all, depending on how various things in your AWS account are set up. It will require tweaking and it will require additional code in order to satisfy your teams needs.

However, what it *does* give is a basic idea of the parts of a CICD pipeline.

As you attempt to utilize this code, there are many comments left behind on places that will need to be updated for your
given stack/account/product. This is not a plug and play feature, but a resource to help teams understand the necessary
steps.

### **RECOMMENDED**

It's highly recommended that a virtual environment be created before installing any pip requirements
* `python3 -m venv .venv` - to create the virtual env
* `source .venv/bin/activate` - to enter the virtual env
* `pip install -U pip` - to upgrade pip
* `pip install -r requirements-dev.txt` to install the requirements into the virtual environment you are in
* `pre-commit install` initialize pre-commit

### **What do you need to set up**
The following things need to be done to customize the contents of this repo to your product.

1. Add to your account a secret in Secret manager titled `deployment` with the keys and corresponding values found in `cdk_configs/product_properties/pipeline_and_deployment_props.py DeploymentSecretKey`
   1. if you don't have all these available, you'll want to strive to get them. In the meantime you can disable portions of the pipeline that rely on them.
2. The Product Settings need to be updated for your particular product. See `cdk_configs/product_properties/common_props.py` for the data that needs to be set to equal your product.
3. The Jira Status update lambda needs to be updated with the proper status IDs. see `common/jira_integration/jira_client.JiraStatus` class for more information.

# **Whats in this repo**

## Pipeline

A simple code pipeline utilizing multiple code builds to run several different types of tests before deploying to production. This is an all in one deployment, not currently a Rolling/BlueGreen/Canary - These will have to be added depending on the teams needs. However, this pipeline does deploy *last* so it will fail and stop if any test fails.

### Source: Codestar

A codestar connection to github will have to be made in your products AWS account. Only one per account is needed, it can handle multiple repos.

### Unit Testing / Integration Testing

Two code builds that simply take the git hub clone from CodeStar and run Pytest. Unit tests are meant to be small, individual function based tests. Integration testing should be tests *between the products internal lambdas* and not external. These are schema/contract style tests for making sure the output of a given lambda continues to work for the input of another lambda.

This is most useful when stringing many lambdas together in Step Functions.

Additionally, the APIs your product provides for other teams to consume should have their schemas tested here. This is just the first line of defense against breaking a contract with another team. Do not rely solely on their tests

### Deploy Adhoc Environment

This stage of the pipeline will deploy a temporary adhoc environment using the production values (but deployed in dev). This environment is to be used for more rigorous testing
### Contract Tests

This is where the te


## .vscode/settings.json

* *editor.rulers* - These add two rulers to vscode. The 88 length one is the line length for Black formatting - lines of code longer than that will be formatted to fit within. the 120 is an arbitrary line for your own purposes if you choose to adjust Black or AutoPep8 Linting

## .pre-commit-config.yaml

This file configures and controls the `pre-commit` which is a tool for automatically adding various git commit hooks to run on every single `git commit` call. There are multiple options - comment out/delete the ones your team does not need:

* *Black* - Black is a linter that is uncompromising. It has virtually no settings to configure, and it always does the same thing no matter what project it lints. This is recommended
* *autopep8 and isort* - The pair of these allows for more configuration by your team on linting through the tox.ini.
  * Find configuration options for autopep8 [here](https://pypi.org/project/autopep8/#configuration)

## cdk_configs

This directory contains all the necessary configuration and props data to configure the CDK stacks to a particular product. The separation of this data from the stack itself allows the stacks to be highly modular and additions or data changes to be easily
reflected in the next deployment without having to update numerous files.

* */resource_names.py* - A set of dataclasses - acting as containers for Constants for making it easier to pass resource names
  * In order to provide common names - especially when calling various resources from another, either with SDK calls (ie boto3) or just between stacks, this file will contain all the names (sans prefix) for the various AWS resources.
  * This also prevents the need to rely on the randomized string of characters CDK applies to a given resource, leaving them with human readable, prefix'd names
  * Names will be combined with a prefix as generated by the DeploymentProperties and passed to the DynamicCDKConfig class for that given resource

* */default_tags.py* - A class for quickly building tag dictionaries to apply to all you resources in a given stack


### cdk_configs/resource_configurations

A directory containing the mappings for various resources. There are two types of files in here: the config classes and structs and config files for specific resources. The config files are arranged with either Maps of configuration settings, in the key:value structure of ResourceName: DynamicCDKConfigs(), or as singletons of just a config class assigned to a variable.

Each DynamicCDKConfigs child has two methods to be used when instantiating it in the stack:

1. First, each configuration before being instantiated needs to have its `update_with_deployment_specific_values()` method called with whatever specific parameters it needs. This function updates the properties of the instantiated class with deployment specific values, such as RemovalPolicy or specific Log Groups.
2. A second method is then called when instantiating the Resource in the stack - `.props()` This returns a dictionary of key:value of the same format as the Resources's kwargs, allowing it to be passed into the resource with `**configObject.props()`

  * */constructs.py* and */common_configs.py*- These contains master definitions for props for CDK Constructs. **This is not extensive** if you use a resource that is not defined in here, and want to make use of the same pattern, you'll need to create your own child classes.
    * `common_configs.py` are simple struct type dataclasses for defining attributes on CDK Constructs that are the same across many different implantation's in your app, such as the runtime environment for lambda, or its memory size, or duration.
    * `constructs.py` is similar to common_configs, but contains the properties for a given CDK Construct that are going to be different each time. The combination of these two allows for an externalized configuration of resources *outside* the stacks, making the cdk stack itself somewhat project agnostic.
    * The dataclasses in here should be defined by Resource and where. Such as PipelineLambda contains the common properties between all pipeline lambdas - such as `runtime` and `memory`.
    * It is important to note, to make best use of this, the attributes MUST be named in the same format (capitalization and all) as their corresponding kwarg from the CDK Construct.
    * If this is done, then the common parent class method of `.props()` can be used in the following format to quickly add the rest of the properties:
    ```python
    config_object = PipelineLambdaConfigs() # with whatever values it needs
    config_object.update_with_deployment_specific_values() # with whatever values this particular resource needs
    myLambda = aws_lambda.Function(
      self, "LogicalId",
      **config_object.props()
    )
    ```

**The following files contain mappings of the configurations to be used by CDK Stacks to keep individual configs out of the stack**
  * */lambda_configs.py* - the configurations for various lambdas making use of classes found in the above mentioned files. Also includes layers
  * */codebuild_configs.py* - Configurations properties for various codebuilds
  * */storage_configs.py* - For storage resources, such as S3, Dynamo

### cdk_configs/product_properties

This directory contains numerous static properties, organized by stack. These include such things as the Github Repo or the Product Name. The purpose again of these files is to reduce typos and have a single easy to change location for these values should the need arise.

* */common_props.py* contains:
  * _DeploymentProperties_ - A master class for deployment options throughout stacks. It should be instantiated in the app.py and passed through to all subsequent nested stacks. It sets several common use checks based on context values when deploying a cdk stack and local env variables
  * _ProductSetting_ - A set of constants related to the Product, such as Team name, repo, branches, ect. Values that do not matter what stack they are in when used, but matter for keeping this product separate from another (and aid if two products share an account)
  * _CloudformationOutputs_ - Key names for the output json from a stack

* */pipeline_and_deployment_props.py* contains:
  * _DeploymentSecretKey_ - Key Names found in the Deployment Secret - for items such as github or jira credentials and vpc identification
  * _ContextTag_ - Tags that can be used and are checked against in the cdk deploy, such as `cdk deploy Stack\* -c deploy_tag=DEV`  - the `deploy_tag` being the value of attributes in ContextTag
  * _DeploymentTag_ Tags that determine what kind of deployment this is, such as DEV, TEST or LOCAL, or PROD. Influence various settings throughout the stack such as retention time on logs or deletion policies on resources
  * _DeploymentFileLocation_ - Paths and names for various files the Stack needs to deploy. Sometimes used in concert with a base_directory path.

In general pipeline_and_deployment_props should contain values that are used in the actual Pipeline Stacks, even though some of them are influenced by deployment type (Dev, Prod, ect)

* */product_properties.py* contains
  * _CommonProductProperties_ Properties that remain the same no matter if hte Product is being deployed in Dev or Prod
  * _ProductionProductProperties_ Production values
  * _DevProductProperties_ Dev values


**Note:** Proper CICD and DevOps practices state NO LONG TERM ENVIRONMENTS / BRANCHES. Technically, having a prod and a dev branch / environment violates this rule, but this is one that its kinda okay to get away with as a necessary evil in our current company maturity.

However.

At no point is it acceptable to add another long living environment - So, at no point is it needed to add any more EnvironmentProperties classes to this file. If you need temporary environments, use the deployment options to deploy a test env and utilize the necessary flags to use the appropriate values for your test. Such environments have a mandate to be destroyed when they are done. On average, it is probably a good idea that no such environment last more than 3 days.


## stacks/pipeline

All the necessary code for the pipeline

* */build_specs* - A set of basic buildspecs for codebuilds

* */nested_stacks* - The nested stacks underneath the pipeline stack
  * */pipeline_codebuilds.py* - Utilizes the codebuild_configs mappings to generate codebuilds for the pipeline
  * */pipeline_lambdas.py* - utilizes the lambda_configs PIPELINE_LAMBDAS to generate lambda's for the pipeline

* */pipeline_lambdas* - The home for lambda's that the pipeline uses
  * */jira_status* - This lambda moves JIRA issues to specific status depending on the steps of the pipeline its called in.
  * */github_tag* - This lambda adds the "prod" tag to the commit that represents the current state of the code in prod at the end of every deployment
  * */snow_approval* - Two lambdas in here, one to initialize a snow ticket, the other to listen for its response and if approved trigger the approval step of the pipeline

## stacks/products

A skeleton for setting up your app.

* */nested_stacks* - The nested stacks underneath the app stack
    * */lambda_stack* - A basic lambda
    * */storage_stack* - A basic s3 and dynamo
    * */api_stack* - A basic API gateway linked to the lambda stack

**Take note:** notice how the API stack uses the `lambda_mapping[ProductLambdaResource.name]` to link to the appropriate lambda. Notice how the lambdas, layers, buckets, and dynamos are defined by the Prop classes in the corresponding files, rather than in the stack itself.

## stacks/tools

Several CDK stacks for various tools.


## aws_lambda_functions/

This directory contains individual directories for each lambda. NOTE - When CDK deploys a particular lambda through the setup in this repo, the directory targeted (the individual directories in this one) become effectively the root of the lambda when deployed! This means your import statements *cannot reference directory structures outside of the individual lambda directory*

This directory is for PRODUCT lambdas, not Pipeline or Tools - those are found in their respective cdk directories to prevent confusion on what is a PROD deployed resource and what is not.

This does cause issues when dealing with local work versus cloud work.

**Remember** You never change the code to work in your local - you change your local to work with what the code already has.

As such, it is **IMPERATIVE** that the import structure not be changed simply to make things work in your local.

Instead, you need to tell your IDE how to use a local PYTHONPATH environment variable that you set up.

See */Documentation/Setting Up Your Local PYTHONPATH.md* for more information.


# Credits

* Anthony Goh - Putting everything together
* Jason Green - For the DevOps direction and what is needed to make a good DevOps pipeline
* Gaurav Tomar - for the prompt/idea to convert to config files and simple, bare bones CDK stacks that read the configs
