import sys
import json
import argparse
import os
from notebooklm_py import NotebookLM

def list_notebooks(token):
    try:
        # Initialize client with token
        client = NotebookLM(token=token)
        notebooks = client.list_notebooks()
        
        results = []
        for nb in notebooks:
            results.append({
                "id": nb.id,
                "title": nb.title,
                "last_modified": str(nb.updated_at)
            })
        
        print(json.dumps({"success": True, "notebooks": results}, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

def get_notebook_details(token, notebook_id):
    try:
        client = NotebookLM(token=token)
        # Fetching specific notebook content (Sources & Notes)
        notebook = client.get_notebook(notebook_id)
        
        sources = []
        for src in notebook.sources:
            sources.append({
                "title": src.title,
                "content": src.text[:2000] + "..." if src.text else ""
            })
            
        notes = []
        for note in notebook.notes:
             notes.append({
                "title": note.title,
                "content": note.text
            })

        print(json.dumps({
            "success": True, 
            "title": notebook.title,
            "sources_count": len(sources),
            "notes_count": len(notes),
            "sources": sources,
            "notes": notes
        }, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["list", "get"], required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--id", help="Notebook ID (required for 'get' action)")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_notebooks(args.token)
    elif args.action == "get":
        if not args.id:
            print(json.dumps({"success": False, "error": "Missing --id for 'get' action"}))
        else:
            get_notebook_details(args.token, args.id)
