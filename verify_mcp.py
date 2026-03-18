import json
import subprocess
import os

server_path = r"C:\Users\emili\AppData\Roaming\Python\Python314\Scripts\notebooklm-mcp-server.exe"

def call_mcp_init():
    process = subprocess.Popen(
        [server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }

    process.stdin.write(json.dumps(init_msg) + "\n")
    response = process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
    
    # Read response
    line = process.stdout.readline()
    init_res = json.loads(line)
    
    # List tools
    list_tools_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    process.stdin.write(json.dumps(list_tools_msg) + "\n")
    
    tools_line = process.stdout.readline()
    tools_res = json.loads(tools_line)
    
    process.terminate()
    return tools_res

try:
    tools_res = call_mcp_init()
    tools = tools_res.get("result", {}).get("tools", [])
    print(f"Total tools: {len(tools)}")
    for t in tools:
        print(f"Tool: {t['name']}")
except Exception as e:
    print(f"Error: {e}")
