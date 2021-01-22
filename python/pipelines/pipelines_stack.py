from aws_cdk import(
  core,
  aws_codepipeline as codepipeline,
  aws_codepipeline_actions as cpactions,
  aws_codecommit as codecommit,
  aws_s3 as s3,
  aws_iam as iam,
  aws_codebuild as codebuild,
  pipelines
)

import json

from application.application import ApplicationStage
from application.constructs.multistagepipeline import MultiStagePipeline

class PipelinesStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  project_cfg: dict, **kwargs):
        super().__init__(scope, id, **kwargs)


        pipeline = MultiStagePipeline(self, 'MultistagePipeline',
            project_cfg = project_cfg
        )

        project_name = project_cfg['Project']['ProjectName']

        deployment_cfg = project_cfg['Deployment']
        for stage_name, stage_cfg in deployment_cfg.items():

            Application = ApplicationStage(self, f'{project_name}{stage_name}',
                env = core.Environment(
                    account= str(stage_cfg['AccountNumber']),
                    region= stage_cfg['Region']
                ),
                stage_name = stage_name,
                project_name = project_name,
                vpc_id = stage_cfg['VpcId']
            )


            if 'ManualApprove' in stage_cfg.keys():

                this_stage = pipeline.pipeline.add_application_stage(
                    app_stage = Application,
                )

                this_stage.add_manual_approval_action(
                    action_name = 'Release_this_Stage',
                    run_order = 1
                )
        
            else:
                pipeline.pipeline.add_application_stage(
                    app_stage = Application,
                )

