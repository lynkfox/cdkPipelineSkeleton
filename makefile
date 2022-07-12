all:
	make pipeline_layer
	make common_layer


pipeline_layer:
	mkdir python
	pip3 install -r layers/requirements-pipeline_layer.txt -t python
	zip -r stacks/pipeline/pipeline_lambdas/pipeline_layer.zip python
	rm -rf python

common_layer:
	mkdir python
	pip3 install -r layers/requirements-common_layer.txt -t python
	cp -R common python
	zip -r aws_lambda_functions/common_layer.zip python
	rm -rf python
