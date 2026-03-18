import json
import subprocess
import os
import sys

# Construct the path dynamically
appdata = os.environ.get('APPDATA')
server_path = os.path.join(appdata, 'Python', 'Python314', 'Scripts', 'notebooklm-mcp-server.exe')

if not os.path.exists(server_path):
    # Try alternate location if Python314 isn't right
    scripts_dir = os.path.join(appdata, 'Python')
    for d in os.listdir(scripts_dir):
        potential = os.path.join(scripts_dir, d, 'Scripts', 'notebooklm-mcp-server.exe')
        if os.path.exists(potential):
            server_path = potential
            break

print(f"Using server at: {server_path}")

def call_mcp(method, params={}):
    process = subprocess.Popen(
        [server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
        shell=True
    )

    # Initialize
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
    # Receive init response
    process.stdout.readline() 
    
    # Notify initialized
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n")
    
    # Call method
    msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": method,
        "params": params
    }
    process.stdin.write(json.dumps(msg) + "\n")
    
    response_line = process.stdout.readline()
    process.terminate()
    return json.loads(response_line)

try:
    # 1. List tools
    tools_res = call_mcp("tools/list")
    tools = tools_res.get("result", {}).get("tools", [])
    print(f"VERIFICATION_START")
    print(f"TOOL_COUNT: {len(tools)}")
    
    create_tool = None
    for t in tools:
        if "create" in t['name'].lower() and "notebook" in t['name'].lower():
            create_tool = t['name']
        # print(f"Tool: {t['name']}")
    
    print(f"CREATE_NOTEBOOK_TOOL: {create_tool}")
    
    # 2. List notebooks (Functional Test)
    notebooks_res = call_mcp("tools/call", {"name": "list_notebooks", "arguments": {}})
    # The output might be in 'content' field
    print(f"NOTEBOOKS_RESULT: {json.dumps(notebooks_res)}")
    print(f"VERIFICATION_END")

except Exception as e:
    print(f"Error during verification: {e}")
