import os
import logging
import time

import boto3

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get("TABLE_NAME")


async def handler(event):
    table = dynamodb.Table(TABLE_NAME)

    timestamp = int(time.time())
    table.put_item(
        Item={
            "Room": "general",
            "Index": 0,
            "Timestamp": timestamp,
            "Username": "ping-user",
            "Content": "PING!",
        }
    )
    logger.debug("Item added to the database.")

    response = {"statusCode": 200, "body": "PONG!"}
    return response

    # const apigwManagementApi = new AWS.ApiGatewayManagementApi({
    #   apiVersion: '2018-11-29',
    #   endpoint: event.requestContext.domainName + '/' + event.requestContext.stage
    # });

    # # const postData = JSON.parse(event.body).data;

    # # const postCalls = connectionData.Items.map(async ({ connectionId }) => {
    # #   try {
    # #     await apigwManagementApi.postToConnection({ ConnectionId: connectionId, Data: postData }).promise();
    # #   } catch (e) {
    # #     if (e.statusCode === 410) {
    # #       console.log(`Found stale connection, deleting ${connectionId}`);
    # #       await ddb.delete({ TableName: TABLE_NAME, Key: { connectionId } }).promise();
    # #     } else {
    # #       throw e;
    # #     }
    # #   }
    # # });

    # # try {
    # #   await Promise.all(postCalls);
    # # } catch (e) {
    # #   return { statusCode: 500, body: e.stack };
    # # }

    # # return { statusCode: 200, body: 'Data sent.' };
