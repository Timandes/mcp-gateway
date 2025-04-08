# MCP Gateway

MCP (Model Context Protocol) Gateway can translate MCP tool callings to traditional HTTP API requests. It can provide a configurable way to get existing HTTP API to MCP territory.



## Getting Started

Create config file from `config.example.yaml`:

```shell
$ cp config.example.yaml config.yaml
```



Edit `config.yaml` file, map all APIs to MCP tools.

Then start launch it with SSE transport:

```shell
$ uv run mcp-gateway
INFO:     Started server process [15400]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
```



Default is 3001.



## Server Control

### Change Port

Provide parameter `--port=<port_no>`  in command line will change the port to SSE transport.

Launch gateway with port 3002:

```shell
$ uv run mcp-gateway --port=3002
INFO:     Started server process [15400]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3002 (Press CTRL+C to quit)
```



### stdio Transport

Provide parameter `--transport=stdio` in command line will change the transport to stdio.

E.G.:

```shell
$ uv run mcp-gateway --transport=stdio
```



It's meaningless to **manually** launch gateway in stdio transport. You can configure in Cursor or Cline like:

```json
{
    "mcpServers": {
        "mcp-gateway": {
          "command": "uv",
          "args": ["run", "mcp-gateway", "--transport=stdio"]
        }
      }
}
```



Or MCP Inspector with form values:

| Item           | Value                             |
| -------------- | --------------------------------- |
| Transport Type | STDIO                             |
| Command        | uv                                |
| Arguments      | run mcp-gateway --transport=stdio |



## Configuration File

There is two parts in configuration YAML, `server` and `tools`. `server` defines the basic info for gateway server use. `tools` defines the mapping from single MCP tool to HTTP API request.

```yaml
server:
  name: rest-amap-server
  config:
    apiKey: foo
tools:
- name: maps-geo
  description: "将详细的结构化地址转换为经纬度坐标。支持对地标性名胜景区、建筑物名称解析为经纬度坐标"
  args:
  - name: address
    description: "待解析的结构化地址信息"
    required: true
  - name: city
    description: "指定查询的城市"
    required: false
  requestTemplate:
    url: "https://restapi.amap.com/v3/geocode/geo?key={{.config.apiKey}}&address={{.args.address}}&city={{.args.city}}&source=ts_mcp"
    method: GET
    headers:
    - key: x-api-key
      value: "{{.config.apiKey}}"
    - key: Content-Type
      value: application/json
  responseTemplate:
    body: |
      # 地理编码信息
      {{- range $index, $geo := .Geocodes }}
      ## 地点 {{add $index 1}}

      - **国家**: {{ $geo.Country }}
      - **省份**: {{ $geo.Province }}
      - **城市**: {{ $geo.City }}
      - **城市代码**: {{ $geo.Citycode }}
      - **区/县**: {{ $geo.District }}
      - **街道**: {{ $geo.Street }}
      - **门牌号**: {{ $geo.Number }}
      - **行政编码**: {{ $geo.Adcode }}
      - **坐标**: {{ $geo.Location }}
      - **级别**: {{ $geo.Level }}
      {{- end }}
```



### Server

| Item   | Description                                                  |
| ------ | ------------------------------------------------------------ |
| name   | Server name                                                  |
| config | Key/Value pairs that can be referenced by var `{{.config.xxx}}` in templates |



### Tools

`tools` is list of MCP tools mapping. Single tool props. are defined as follows:

| Item             | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| name             | Tool name (Function name), which is provided to LLM.         |
| description      | Tool description through which LLM can understand what the tool could do. |
| args             | Arguments of tool (Function arguments).                      |
| requestTemplate  | Request mapping to target HTTP API.                          |
| responseTemplate | Response mapping for response of target HTTP API.            |



Single argument props. are defined as follows:

| Item        | Type    | Description                                                  |
| ----------- | ------- | ------------------------------------------------------------ |
| name        |         | Argument name, which is provided to LLM.                     |
| description |         | Argument description through which LLM can understand and decide what value should be filled. |
| required    | Boolean | Required argument or not.                                    |



Request template props. are defined as follows:

| Item    | Description                  |
| ------- | ---------------------------- |
| method  | HTTP method                  |
| url     | Target HTTP API url template |
| headers | HTTP headers                 |



HTTP headers are defined as follows:

| Item  | Description           |
| ----- | --------------------- |
| key   | Header key            |
| value | Header value template |



Response template props are defined as follows:

| Item | Description            |
| ---- | ---------------------- |
| body | Response body template |



## Contribution

All kinds of contribution are welcomed.
