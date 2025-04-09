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
#     import tracemalloc
#
#     tracemalloc.start()
#     payload = {"vcs_type": "bitbucket_2", "pr_id": "120", "workspace_id": "35", "repo_name": "athena-service"}
#     await AzureBusServiceGenAiSubscriber(config).publish(payload.copy())
#     # await AzureBusServiceGenAiSubscriber(config).subscribe()
#     # import asyncio
#     # tasks_1 = []
#     # tasks_2 = []
#     # for i in range(10):
#     #     payload["pr_id"] = str(i)
#     #     payload["msg"] = 1
#     #     tasks_1.append(AzureBusServiceGenAiSubscriber(config).publish(payload.copy()))
#     #     payload["msg"] = 2
#     #     tasks_2.append(AzureBusServiceGenAiSubscriber(config).publish(payload.copy()))
#     # await asyncio.gather(*tasks_1)
#     # await asyncio.gather(*tasks_2)
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
