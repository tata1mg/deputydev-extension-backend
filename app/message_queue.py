# from deputydev_core.utils.config_manager import ConfigManager
# ConfigManager.initialize()
# from app.main.blueprints.deputy_dev.services.message_queue.genai.azure_bus_service_genai_subscriber import (
#     AzureBusServiceGenAiSubscriber,
# )
# import asyncio
# from torpedo import CONFIG
#
# config = CONFIG.config
#
# NAMESPACE_FQDN = "deputydevreviewnamespacev2.servicebus.windows.net"
# AZURE_QUEUE_NAME = "code-review-dummy"
# SUBSCRIPTION_ID = "cc4bf225-28b4-467a-b27b-c0efe9857540"
# NAMESPACE = "deputydevreviewnamespacev2"
# RESOURCE_GROUP = "deputyDev"
#
# # config = {
# #     "AZURE_BUS_SERVICE": {
# #         "NAMESPACE": NAMESPACE,
# #         "NAMESPACE_FQDN": NAMESPACE_FQDN,
# #         "LOGGING_ENABLED": True,
# #         "SUBSCRIPTION_ID": SUBSCRIPTION_ID,
# #         "RESOURCE_GROUP": RESOURCE_GROUP,
# #     }
# # }
#
#
# async def main():
#     payload = {"vcs_type": "bitbucket", "pr_id": "12", "workspace_id": "34", "repo_name": "athena-service"}
#     await AzureBusServiceGenAiSubscriber(config).subscribe()
#     # await AzureBusServiceGenAiSubscriber(config).publish(payload)
#     # queue_manager = AzureServiceBusManager(config)
#     # await queue_manager.get_client(AZURE_QUEUE_NAME)
#     # try:
#     #     payload = "Hello honey bunny"
#     #     await queue_manager.publish(payload=payload, session_id="hello", message_id="hello_1")
#     #     await queue_manager.publish(payload=payload, session_id="hello", message_id="hello_1")
#     #     await queue_manager.publish(payload=payload, session_id="hello", message_id="hello_2")
#     #     await queue_manager.subscribe(max_message_count=10)
#     # except Exception as error:
#     #     pass
#     # finally:
#     #     await queue_manager.close()
#
#
# asyncio.run(main())
