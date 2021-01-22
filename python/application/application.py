from aws_cdk import(
    core,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2
)


class ApplicationStage(core.Stage):
    def __init__(self, scope: core.Construct, id: str, *, stage_name: str, project_name: str, vpc_id, **kwargs):
        super().__init__(scope, id, **kwargs)

        Application = ApplicationStack(self, 'Application',
            stage_name=stage_name,
            project_name=project_name,
            vpc_id = vpc_id
        )

class ApplicationStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, *, stage_name: str, project_name: str, vpc_id, **kwargs):
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, 'vpc',
            vpc_id = vpc_id
        )

        loadbalancer = elbv2.ApplicationLoadBalancer(self, 'loadbalancer',
            vpc = vpc,
            internet_facing = False
        )

