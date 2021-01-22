#!/usr/bin/env python3

from aws_cdk import core
from pipelines.pipelines_stack import PipelinesStack

import yaml

with open('config/project.yaml') as project_cfg_yaml:
    project_cfg = yaml.load(project_cfg_yaml, Loader=yaml.FullLoader)

app = core.App()

PipelinesStack(app, "PipelinePattern",
    project_cfg = project_cfg,
    env = core.Environment(
        account = project_cfg['Pipeline']['Account'],
        region  =  project_cfg['Pipeline']['Region']
    )
)


app.synth()



