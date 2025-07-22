"""
   Copyright 2025 Timandes White

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import os

import anyio
import click
import httpx

import mcp.types as types
from mcp.server.lowlevel import Server

from loader import load_config

async def forward_tool_call(
    method: str, url: str,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        response = await client.request(method, url)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]

@click.command()
@click.option("--port", default=3001, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="sse",
    help="Transport type",
)
@click.option("--api-key", envvar="HOME_ASSISTANT_API_KEY", default="", help="Long-Lived Access Token from Home Assistant")
@click.option("--baseurl", envvar="HOME_ASSISTANT_BASE_URL", default="http://localhost:8123", help="Base url for Home Assistant")
def main(port: int, transport: str, api_key: str, baseurl: str) -> int:
    app = Server("mcp-gateway")

    config = load_config("config.yaml")

    tools = []
    tools_map = {}
    for tool in config["tools"]:
        props = {}
        for arg in tool["args"]:
            props[arg["name"]] = {
                "type": "string",
                "description": arg["description"],
            }
        tools.append(types.Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema={
                    "type": "object",
                    #"required": ["url"],
                    "properties": props,
                },
            ))
        tools_map[tool["name"]] = tool

    @app.call_tool()
    async def fetch_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name not in tools_map:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = tools_map[name]
        if "requestTemplate" not in tool:
            raise ValueError(f"Tool {name} does not have a requestTemplate")
        url = tool["requestTemplate"]["url"]
        for k, v in arguments.items():
            url = url.replace("{{.args." + k + "}}", v)
        for k, v in config["server"]["config"].items():
            url = url.replace("{{.config." + k + "}}", v)
        #return [types.TextContent(type="text", text=url)]

        return await forward_tool_call(tool["requestTemplate"]["method"], url)

        # if name == "get_entity_state":
        #     if "entity_id" not in arguments:
        #         raise ValueError("Missing required argument 'entity_id'")
        #     return await get_entity_state(arguments["entity_id"], apikey=api_key, baseurl=baseurl)
        # if name == "list_states":
        #     return await list_states(apikey=api_key, baseurl=baseurl)
        # if name == "fetch":
        #     if "url" not in arguments:
        #         raise ValueError("Missing required argument 'url'")
        #     return await fetch_website(arguments["url"])
        # raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return tools

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport(os.getenv("MESSAGE_PATH","/messages/"))

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount(os.getenv("MESSAGE_PATH","/messages/"), app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0
