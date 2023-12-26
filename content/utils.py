import asyncio
import js
import os
import datetime as dt
from js import Object
from js import fetch
from pyodide.ffi import to_js

from pyodide.http import pyfetch

# Ish via https://til.simonwillison.net/python/sqlite-in-pyodide
from pyodide.http import open_url

DB_NAME = "JupyterLite Storage"
    
# Via: https://github.com/jupyterlite/jupyterlite/discussions/91#discussioncomment-1137213
async def get_contents(store, path, raw=False):
    """Load file from in-browser storage. Contents are in ['content'].
    
    Use the IndexedDB API to access JupyterLite's in-browser (for now) storage
    
    For documentation purposes, the full names of the JS API objects are used.
    
    See https://developer.mozilla.org/en-US/docs/Web/API/IDBRequest
    """
    # we only ever expect one result, either an error _or_ success
    queue = asyncio.Queue(1)
    
    IDBOpenDBRequest = js.self.indexedDB.open(DB_NAME)
    IDBOpenDBRequest.onsuccess = IDBOpenDBRequest.onerror = queue.put_nowait
    
    await queue.get()
    
    if IDBOpenDBRequest.result is None:
        return None
        
    IDBTransaction = IDBOpenDBRequest.result.transaction(store, "readonly")
    IDBObjectStore = IDBTransaction.objectStore(store)
    IDBRequest = IDBObjectStore.get(path, "key")
    IDBRequest.onsuccess = IDBRequest.onerror = queue.put_nowait
    
    await queue.get()
    
    response = IDBRequest.result.to_py() if IDBRequest.result else None

    if raw:
        return response
    else:
        return response['content'] if response else None


# via https://github.com/jupyterlite/jupyterlite/discussions/91#discussioncomment-2440964
async def put_contents(content, store, path, overwrite=False):
    """
    """
    # count existing
    queue = asyncio.Queue(1)
    
    IDBOpenDBRequest = js.self.indexedDB.open(DB_NAME)
    IDBOpenDBRequest.onsuccess = IDBOpenDBRequest.onerror = queue.put_nowait
    await queue.get()
    
    if IDBOpenDBRequest.result is None:
        return None
        
    IDBTransaction = IDBOpenDBRequest.result.transaction(store, "readonly")
    IDBObjectStore = IDBTransaction.objectStore(store)
    IDBRequest = IDBObjectStore.count(path)
    
    IDBRequest.onsuccess = IDBRequest.onerror = queue.put_nowait
    await queue.get()
    
    count = IDBRequest.result
    # print(f'count = {count}')
    
    if count == 1 and not overwrite:
        print(f'file {path} exists - will not overwrite')
        return 
    
    # add file
    value = {
        'name': os.path.basename(path), 
        'path': path,
        'format': 'text',
        'created': dt.datetime.now().isoformat(),
        'last_modified': dt.datetime.now().isoformat(),
        'content': content,
        'mimetype': 'text/plain',
        'type': 'file',
        'writable': True,
    }
    #print(value)

    IDBTransaction = IDBOpenDBRequest.result.transaction(store, "readwrite")
    IDBObjectStore = IDBTransaction.objectStore(store)
    # see https://github.com/pyodide/pyodide/issues/1529#issuecomment-905819520
    value_as_js_obj = to_js(value, dict_converter=Object.fromEntries)
    if count == 0:
        IDBRequest = IDBObjectStore.add(value_as_js_obj, path)
    if count == 1:
        IDBRequest = IDBObjectStore.put(value_as_js_obj, path)
    IDBRequest.oncomplete = IDBRequest.onsuccess = IDBRequest.onerror = queue.put_nowait
    await queue.get()
    
    return IDBRequest.result
