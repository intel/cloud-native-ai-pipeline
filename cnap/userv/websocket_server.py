"""A WebSocket Server module.

The WebSocket Server subscribes to all inferred streams from the Redis broker and hosts a WebSocket
server to publish the streams to an HTML5 based front-end SPA (Single Page Application).

It is based on asyncio and coroutine programming models since most operations are IO bound.

Classes:
    StreamWebSocketServer: A class for Stream WebSocket Server to publish streams via WebSocket
      from the broker.
"""

import os
import sys
import asyncio
import logging
import signal
import http
from typing import Any, Optional

import redis.asyncio as redis
import websockets.exceptions
import websockets.server

LOG = logging.getLogger(__name__)

STREAM_WEBSOCKET_PORT = 31611
PIPELINE_TABLE = "Pipeline-table"
MAX_RECONNECTION_TIMES = 5
MAX_CLIENT_CONNECTIONS = 100

class StreamWebSocketServer:
    """A class for Stream WebSocket Server to publish streams via WebSocket from the broker.

    Attributes:
        _stream_broker_redis_host (str): The host ip or hostname of stream broker Redis server.
        _stream_broker_redis_port (int): The host port of stream broker Redis server.
        _pipelines (dict): A dictionary object representing the stream publish tasks for every
          pipelines.
        _users (dict): A dictionary object representing all established WebSocket connections.
    """

    def __init__(self):
        """Initialize a StreamWebSocketServer object."""
        self._stream_broker_redis_host = self._get_env(
            "STREAM_BROKER_REDIS_HOST", "127.0.0.1")
        self._stream_broker_redis_port = self._get_env(
            "STREAM_BROKER_REDIS_PORT", 6379)
        self._pipelines = {}
        self._users = {}

    @staticmethod
    def _get_env(key, default: Optional[Any]=None) -> Optional[Any]:
        """Get environment variable.

        Args:
            key (str): The name of the environment variable.
            default (Optional[Any]): The default value to return if the environment variable
                does not exist.

        Returns:
            Optional[Any]: The value of the environment variable or the default value.
        """
        if key not in os.environ:
            LOG.warning("Could not find the key %s in the environment, "
                        "use default value %s", key, str(default))
            return default
        return os.environ[key]

    def _add_pipeline(self, sid: str):
        """Add pipeline.

        Args:
            sid (str): The id of pipeline to add.
        """
        LOG.info("add pipeline: %s", sid)
        self._pipelines[sid] = asyncio.get_event_loop().create_task(
            self._stream_publish_task(sid))

    def _del_pipeline(self, sid: str):
        """Delete pipeline.

        Args:
            sid (str): the id of pipeline to delete.
        """
        LOG.info("remove pipeline: %s", sid)
        self._pipelines[sid].cancel()
        del self._pipelines[sid]

    def _on_update(self, pipeline_list: list):
        """Update pipelines.

        Args:
            pipeline_list (list): The list of pipeline ids to update.
        """
        for new_item in pipeline_list:
            if new_item not in self._pipelines:
                self._add_pipeline(new_item)

        for old_item in list(self._pipelines.keys()):
            if old_item not in pipeline_list:
                self._del_pipeline(old_item)

    async def _websocket_server_task(self, wsobj: websockets.server.WebSocketServerProtocol,
                                     path: str):
        """Connection handler for websocket server connection.

        Args:
            wsobj (websockets.server.WebSocketServerProtocol): The WebSocketServerProtocol object
              for websocket server connection.
            path (str): The path for websocket server connection.
        """
        LOG.info("WebSocket server task start: %s path: %s", str(wsobj), path)
        target = path[1:]  # skip / prefix

        if len(list(self._users.keys())) > MAX_CLIENT_CONNECTIONS:
            LOG.error("Exceed the max number of client connections: 100.")
            return

        self._users[wsobj] = target
        try:
            while True:
                try:
                    _ = await wsobj.recv()
                except asyncio.CancelledError:
                    LOG.error("WebSocket task cancelled, %s", target)
                    break
                except websockets.exceptions.ConnectionClosedError:
                    LOG.error("WebSocket connection closed [error], %s", target)
                    break
                except websockets.exceptions.ConnectionClosedOK:
                    LOG.error("WebSocket connection closed [ok], %s", target)
                    break
        finally:
            del self._users[wsobj]
            LOG.info("WebSocket server task stop.")

    async def _pipeline_status_monitor_task(self):
        """Pipelines status monitor task, monitor and update pipelines."""
        LOG.info("Task pipeline status monitor task start.")

        try:
            redis_conn = redis.Redis(host=self._stream_broker_redis_host,
                            port=self._stream_broker_redis_port,
                            encoding='utf-8', decode_responses=True)
        except ConnectionRefusedError:
            LOG.error("Fail to connect to Redis host.", exc_info=True)
            sys.exit(1)

        reconnect_count = 0
        sleep_time = 0.5

        try:
            while True:
                try:
                    self._on_update(await redis_conn.execute_command("HKEYS",
                            PIPELINE_TABLE))
                except redis.ConnectionError as e:
                    LOG.error("redis connection error: %s", e)
                    LOG.info("reconnect to redis server")

                    # Sleep before reconnect, double the sleep time per reconnection.
                    sleep_time *= 2

                    await asyncio.sleep(sleep_time)

                    # Connect to redis server
                    redis_conn = redis.Redis(host=self._stream_broker_redis_host,
                            port=self._stream_broker_redis_port,
                            encoding='utf-8', decode_responses=True)

                    reconnect_count += 1

                    if reconnect_count > MAX_RECONNECTION_TIMES:
                        LOG.error("Continuously reconnect to redis server more than %d times, \
                                  Redis host closed.", MAX_RECONNECTION_TIMES, exc_info=True)
                        sys.exit(1)
                    else:
                        continue
                reconnect_count = 0
                sleep_time = 0.5
                await asyncio.sleep(1)
        finally:
            await redis_conn.close()
            LOG.info("Task pipeline status monitor task stop.")

    async def _connect_subscribe(self, topic: str):
        """Connect to redis server and subscribe topic.

        Args:
            topic (str): The topic to subscribe.
        """
        redis_conn = redis.Redis(host=self._stream_broker_redis_host,
                            port=self._stream_broker_redis_port)
        redis_pubsub = redis_conn.pubsub()
        await redis_pubsub.subscribe(topic)
        response = await redis_pubsub.get_message(timeout=None)
        if response is None or response["type"] != "subscribe":
            LOG.error("Failed to subscribe %s", topic)
        else:
            LOG.info("subscribe %s successfully", topic)
        return redis_conn, redis_pubsub

    async def _stream_publish_task(self, sid: str):
        """Stream publish task, subscribe result streams and publish to spa.

        Args:
            sid (str): The id of pipeline to publish result stream.
        """
        LOG.info("stream publish task start: %s", sid)

        # Get the topic name from Redis with the pipeline id(sid)
        topic = "result-" + sid

        # Connect to redis server and subscribe the topic
        redis_conn, redis_pubsub = await self._connect_subscribe(topic)

        # The reconnect counter
        reconnect_count = 0

        sleep_time = 0.5

        try:
            while True:
                try:
                    msg = await redis_pubsub.get_message(timeout=None)
                except redis.ConnectionError as e:
                    LOG.error("[%s] redis connection error: %s", sid, e)
                    LOG.info("[%s] reconnect to redis server", sid)

                    # Sleep before reconnect, double the sleep time per reconnection.
                    sleep_time *= 2

                    await asyncio.sleep(sleep_time)

                    # Connect to redis server and subscribe the topic
                    redis_conn, redis_pubsub = await self._connect_subscribe(topic)

                    reconnect_count += 1

                    if reconnect_count <= MAX_RECONNECTION_TIMES:
                        continue

                    LOG.error("[%s] continuously reconnect to redis server more than %d times",
                            sid, MAX_RECONNECTION_TIMES)
                    break
                reconnect_count = 0
                sleep_time = 0.5

                if msg is None:
                    LOG.info("message for %s is None", topic)
                    break
                if isinstance(msg["data"], bytes):
                    for user in list(self._users.keys()):
                        if user not in self._users or self._users[user] != sid:
                            continue

                        try:
                            await user.send(msg["data"])
                        except websockets.exceptions.ConnectionClosedOK:
                            LOG.error("[%s] fail to send due to WebSocket exception [cc_ok]",
                                    sid)
                        except websockets.exceptions.ConnectionClosedError:
                            LOG.error("[%s] fail to send due to WebSocket exception [cc_error]",
                                    sid)
                        except websockets.exceptions.WebSocketException:
                            LOG.error("[%s] Uncatched websockets error",
                                    sid, exc_info=True)
        finally:
            await redis_pubsub.close()
            await redis_conn.close()
            LOG.info("stream publish task stop for sid: %s", sid)

    async def _health_check(self, path, request_headers):
        """Access `/healthz` path to check the health of websocket server."""
        if path == "/healthz":
            return http.HTTPStatus.OK, [], b"OK\n"

    async def _start_ws_server(self):
        """Start websocket server."""
        ws_server = await websockets.server.serve(
                        self._websocket_server_task,
                        "0.0.0.0",
                        STREAM_WEBSOCKET_PORT,
                        process_request=self._health_check)
        await ws_server.wait_closed()

    async def _shutdown(self, sigobj: signal.Signals, loop: asyncio.AbstractEventLoop):
        """Shut down websocket server.

        Args:
            sigobj (signal.Signals): The shut down signal.
            loop (asyncio.AbstractEventLoop): The asyncio event loop.
        """
        LOG.info("Received exit signal %s...", sigobj.name)
        tasks = [task for task in asyncio.all_tasks() if task is not
                asyncio.tasks.current_task()]
        list(map(lambda task: task.cancel(), tasks))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        LOG.info('finished awaiting cancelled tasks, results: %s', results)
        loop.stop()

    def run(self):
        """The main entry of WebSocket Server."""
        loop = asyncio.get_event_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for sigobj in signals:
            loop.add_signal_handler(
                sigobj,
                lambda sigobj=sigobj: loop.create_task(
                    self._shutdown(sigobj, loop)))

        try:
            loop.create_task(self._pipeline_status_monitor_task())
            loop.create_task(self._start_ws_server())
            loop.run_forever()
        finally:
            loop.close()
            logging.info("Successfully shutdown.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(threadName)s %(message)s")
    SWSS = StreamWebSocketServer()
    SWSS.run()
