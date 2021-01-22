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


class PipelinesStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  project_cfg: dict,   **kwargs):
        super().__init__(scope, id, **kwargs)

        project_name = project_cfg['Project']['ProjectName']
        

        # create a source for the pipeline 
        pipeline_src_cfg = project_cfg['Pipeline']['Source']

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

        if 'S3' in pipeline_src_cfg.keys():
            source_bucket = s3.Bucket(self,'S3sourcebucket',
                bucket_name = pipeline_src_cfg['S3']['BucketName'],
                versioned = True
            )
            pipeline_source_action = cpactions.S3SourceAction(
                action_name="S3Source",
                bucket=source_bucket,
                bucket_key="source/source.zip",
                output=source_artifact,
            )
            if 'IAMUser' in pipeline_src_cfg['S3'].keys():
                # create a user: Note you still need to give this user some credentials, via the console
                # or CLI
                bucket_iam_user = iam.User(self, 's3iamaccount',
                    user_name =  pipeline_src_cfg['S3']['IAMUser']
                )
                source_bucket.grant_read_write(identity=bucket_iam_user)

        if 'GitHub' in pipeline_src_cfg.keys():  # TODO
            print('do something')
        
        if 'CodeCommit' in pipeline_src_cfg.keys():

            source_repo = codecommit.Repository(self, project_name + 'codecommit',
                repository_name = pipeline_src_cfg['CodeCommit']['RepoName'],
                description =  pipeline_src_cfg['CodeCommit']['RepoDescription'],
            )

            pipeline_source_action = cpactions.CodeCommitSourceAction(
                output = source_artifact,
                repository = source_repo,
                branch = pipeline_src_cfg['CodeCommit']['Branch'],
                trigger = cpactions.CodeCommitTrigger.EVENTS,
                action_name = 'OnRepoevent',
                run_order= 1
            )
        # Create the synth action. 
        
        # build a set of profiles to use. ( will use the bootstrap role)


        with open('cdk.json') as cdk_json:
            cdk = json.load(cdk_json)

        bootstrap = cdk['context']['@aws-cdk/core:bootstrapQualifier']
        
        synth_accounts = ''

        #cdk-fudawl-cfn-exec-role-259661075734-ap-southeast-2

        profiles = open('.aws/config', 'w')
        for name, account in project_cfg['Deployment'].items():
            profiles.write(f'[profile {name}]\n')
            bootstrap_role = f"cdk-{bootstrap}-cfn-exec-role-{account['AccountNumber']}-{account['Region']}"
            profiles.write(f"role_arn = arn:aws:iam::{account['AccountNumber']}:role/{bootstrap_role}\n")
            profiles.write(f"region = {account['Region']}\n")
            profiles.write(f"credential_source = Ec2InstanceMetadata\n")
            profiles.write(f"\n") 
            synth_accounts += ' && cdk synth --profile ' + name
        profiles.close()
 
        pipeline_synth_cfg = project_cfg['Pipeline']['Synth']
    
        additional_policy = []
        if 'AdditionalPolicy' in pipeline_synth_cfg.keys():
            for statement in pipeline_synth_cfg['AdditionalPolicy']:
                if statement['effect'] == 'ALLOW':
                    effect = iam.Effect.ALLOW
                else:
                    effect = iam.Effect.DENY

                additional_policy.append(
                    iam.PolicyStatement(
                        actions = statement['actions'],
                        resources = statement['resources'],
                        effect = effect
                    )
                )

        synth_action = pipelines.SimpleSynthAction(
            source_artifact=source_artifact,    
            cloud_assembly_artifact=cloud_assembly_artifact,
            install_command='npm install -g aws-cdk && pip install -r requirements.txt',
            synth_command = 'cdk synth' + synth_accounts + ' && cp cdk.json cdk.out',
            role_policy_statements = additional_policy,
            environment = codebuild.BuildEnvironment(
                privileged = pipeline_synth_cfg['Environment']['Privileged']
            )
        )

        pipeline = pipelines.CdkPipeline(self, project_name + 'Pipeline',
            cloud_assembly_artifact = cloud_assembly_artifact,
            pipeline_name = f'{project_name}pipeline',
            source_action = pipeline_source_action,
            synth_action = synth_action,
            self_mutating = True,
        )

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

            manual_approval = False

            if 'ManualApprove' in stage_cfg.keys():

                this_stage = pipeline.add_application_stage(
                    app_stage = Application,
                )

                this_stage.add_manual_approval_action(
                    action_name = 'Release_this_Stage',
                    run_order = 1
                )
        
            else:
                pipeline.add_application_stage(
                    app_stage = Application,
                )

