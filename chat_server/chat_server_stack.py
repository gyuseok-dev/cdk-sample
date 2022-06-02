from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigatewayv2 as _apigw,
    RemovalPolicy,
)
from constructs import Construct


config = {"stage": "dev", "region": "ap-southeast-2", "account_id": ""}


class ChatServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table_name = "simplechat_connections"
        name = f"{construct_id}-api"
        api = _apigw.CfnApi(
            self,
            name,
            name="ChatAppApi",
            protocol_type="WEBSOCKET",
            route_selection_expression="$request.body.action",
        )
        table = dynamodb.Table(
            self,
            f"{name}-table",
            table_name=table_name,
            partition_key=dynamodb.Attribute(
                name="connectionId", type=dynamodb.AttributeType.STRING
            ),
            read_capacity=5,
            write_capacity=5,
            removal_policy=RemovalPolicy.DESTROY,
        )

        connect_func = _lambda.Function(
            self,
            "connect-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="app.handler",
            code=_lambda.Code.from_asset("./lambda/onconnect"),
            timeout=Duration.seconds(300),
            memory_size=256,
            environment={"TABLE_NAME": table_name},
        )

        table.grant_read_write_data(connect_func)

        disconnect_func = _lambda.Function(
            self,
            "disconnect-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="app.handler",
            code=_lambda.Code.from_asset("./lambda/ondisconnect"),
            timeout=Duration.seconds(300),
            memory_size=256,
            environment={"TABLE_NAME": table_name},
        )
        table.grant_read_write_data(connect_func)

        message_func = _lambda.Function(
            self,
            "message-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="app.handler",
            code=_lambda.Code.from_asset("./lambda/sendmessage"),
            timeout=Duration.seconds(300),
            memory_size=256,
            initial_policy=[
                iam.PolicyStatement(
                    actions=["execute-api:ManageConnections"],
                    resources=[
                        f"arn:aws:execute-api:{config['region']}:{config['account_id']}:{api.ref}/*"
                    ],
                    effect=iam.Effect.ALLOW,
                )
            ],
            environment={"TABLE_NAME": table_name},
        )
        table.grant_read_write_data(message_func)

        # access role for the socket api to access the socket lambda
        policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=[
                connect_func.function_arn,
                disconnect_func.function_arn,
                message_func.function_arn,
            ],
            actions=["lambda:InvokeFunction"],
        )
        role = iam.Role(
            self,
            f"{name}-iam-role",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        )
        role.add_to_policy(policy)

        # lambda integration
        connect_integration = _apigw.CfnIntegration(
            self,
            "connect-lambda-integration",
            api_id=api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{config['region']}:lambda:path/2015-03-31/functions/{connect_func.function_arn}/invocations",
            credentials_arn=role.role_arn,
        )
        disconnect_integration = _apigw.CfnIntegration(
            self,
            "disconnect-lambda-integration",
            api_id=api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{config['region']}:lambda:path/2015-03-31/functions/{disconnect_func.function_arn}/invocations",
            credentials_arn=role.role_arn,
        )
        message_integration = _apigw.CfnIntegration(
            self,
            "message-lambda-integration",
            api_id=api.ref,
            integration_type="AWS_PROXY",
            integration_uri=f"arn:aws:apigateway:{config['region']}:lambda:path/2015-03-31/functions/{message_func.function_arn}/invocations",
            credentials_arn=role.role_arn,
        )

        connect_route = _apigw.CfnRoute(
            self,
            "connect-route",
            api_id=api.ref,
            route_key="$connect",
            authorization_type="NONE",
            target=f"integrations/{connect_integration.ref}",
        )
        disconnect_route = _apigw.CfnRoute(
            self,
            "disconnect-route",
            api_id=api.ref,
            route_key="$disconnect",
            authorization_type="NONE",
            target=f"integrations/{disconnect_integration.ref}",
        )
        # message_route = _apigw.CfnRoute(
        #     self,
        #     "message-route",
        #     api_id=api.ref,
        #     route_key="$sendmessage",
        #     authorization_type="NONE",
        #     target=f"integrations/{message_integration.ref}",
        # )

        deployment = _apigw.CfnDeployment(
            self, f"{name}-deployment", api_id=api.ref
        )
        _apigw.CfnStage(
            self,
            f"{name}-stage",
            api_id=api.ref,
            auto_deploy=True,
            deployment_id=deployment.ref,
            stage_name="dev",
        )
        deployment.node.add_dependency(connect_route)
        deployment.node.add_dependency(disconnect_route)
        # deployment.node.add_dependency(message_route)
        # The code that defines your stack goes here
