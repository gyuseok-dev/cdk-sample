import aws_cdk as core
import aws_cdk.assertions as assertions

from chat_server.chat_server_stack import ChatServerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in chat_server/chat_server_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ChatServerStack(app, "chat-server")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
