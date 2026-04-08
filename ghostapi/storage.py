"""Pluggable storage system for ghostapi."""

import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a value by key."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all values."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all data."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage backend (default)."""
    
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = value
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._data.values())
    
    def clear(self) -> None:
        self._data.clear()


class FileStorage(StorageBackend):
    """File-based JSON storage backend."""
    
    def __init__(self, file_path: str = "ghostapi_data.json") -> None:
        # Validate and sanitize file path to prevent path traversal
        self.file_path = self._sanitize_path(file_path)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _sanitize_path(self, file_path: str) -> str:
        """
        Sanitize file path to prevent path traversal attacks.
        
        Args:
            file_path: The user-provided file path.
        
        Returns:
            Sanitized absolute path within allowed directory.
        
        Raises:
            ValueError: If path attempts directory traversal.
        """
        # Get absolute path and resolve any symlinks
        abs_path = os.path.abspath(file_path)
        
        # Check for path traversal attempts
        if ".." in file_path or os.path.isabs(file_path):
            # Only allow relative paths in current directory
            filename = os.path.basename(file_path)
            abs_path = os.path.abspath(filename)
        
        # Allow only files in current working directory
        cwd = os.path.abspath(os.getcwd())
        if not abs_path.startswith(cwd):
            # If outside cwd, use default in cwd
            abs_path = os.path.join(cwd, os.path.basename(file_path))
        
        return abs_path
    
    def _load(self) -> None:
        """Load data from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
    
    def _save(self) -> None:
        """Save data to file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self._data, f, indent=2)
        except IOError:
            pass  # Silent fail for file write errors
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = value
        self._save()
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False
    
    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._data.values())
    
    def clear(self) -> None:
        self._data.clear()
        self._save()


class BufferedFileStorage(StorageBackend):
    """
    File-based storage with write-behind buffering.
    
    Improves performance by batching writes instead of saving on every change.
    """
    
    def __init__(
        self,
        file_path: str = "ghostapi_data.json",
        buffer_size: int = 10,
        flush_interval: float = 5.0
    ) -> None:
        self.file_path = self._sanitize_path(file_path)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._pending_writes = 0
        self._last_flush = 0
        self._dirty = False
        self._load()
    
    def _sanitize_path(self, file_path: str) -> str:
        """Sanitize file path."""
        abs_path = os.path.abspath(file_path)
        if ".." in file_path or os.path.isabs(file_path):
            filename = os.path.basename(file_path)
            abs_path = os.path.abspath(filename)
        cwd = os.path.abspath(os.getcwd())
        if not abs_path.startswith(cwd):
            abs_path = os.path.join(cwd, os.path.basename(file_path))
        return abs_path
    
    def _load(self) -> None:
        """Load data from file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
    
    def _should_flush(self) -> bool:
        """Check if we should flush the buffer."""
        if self._pending_writes >= self._buffer_size:
            return True
        if time.time() - self._last_flush >= self._flush_interval:
            return True
        return False
    
    def _flush(self) -> None:
        """Flush data to file."""
        if self._dirty:
            try:
                # Write to temp file first, then rename (atomic)
                temp_path = self.file_path + ".tmp"
                with open(temp_path, 'w') as f:
                    json.dump(self._data, f, indent=2)
                os.replace(temp_path, self.file_path)
                self._dirty = False
                self._pending_writes = 0
                self._last_flush = time.time()
            except IOError:
                pass
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = value
        self._dirty = True
        self._pending_writes += 1
        
        if self._should_flush():
            self._flush()
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._dirty = True
            self._pending_writes += 1
            
            if self._should_flush():
                self._flush()
            return True
        return False
    
    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._data.values())
    
    def clear(self) -> None:
        self._data.clear()
        self._dirty = True
        self._flush()
    
    def flush(self) -> None:
        """Force flush pending writes."""
        self._flush()


class AsyncFileStorage(StorageBackend):
    """
    Async file-based storage with aiofiles.
    
    Non-blocking file I/O for better performance under load.
    """
    
    def __init__(self, file_path: str = "ghostapi_async_data.json") -> None:
        self.file_path = self._sanitize_path(file_path)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._load_sync()
    
    def _sanitize_path(self, file_path: str) -> str:
        """Sanitize file path."""
        abs_path = os.path.abspath(file_path)
        if ".." in file_path or os.path.isabs(file_path):
            filename = os.path.basename(file_path)
            abs_path = os.path.abspath(filename)
        cwd = os.path.abspath(os.getcwd())
        if not abs_path.startswith(cwd):
            abs_path = os.path.join(cwd, os.path.basename(file_path))
        return abs_path
    
    def _load_sync(self) -> None:
        """Load data synchronously (for init)."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
    
    async def _load(self) -> None:
        """Load data asynchronously."""
        try:
            import aiofiles
            async with aiofiles.open(self.file_path, 'r') as f:
                content = await f.read()
                self._data = json.loads(content) if content else {}
        except (json.JSONDecodeError, IOError, ImportError):
            self._data = {}
    
    async def _save(self) -> None:
        """Save data asynchronously."""
        try:
            import aiofiles
            temp_path = self.file_path + ".tmp"
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(self._data, indent=2))
            os.replace(temp_path, self.file_path)
        except (IOError, ImportError):
            # Fallback to sync
            with open(self.file_path, 'w') as f:
                json.dump(self._data, f, indent=2)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = value
        # Schedule async save
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._save())
            else:
                loop.run_until_complete(self._save())
        except Exception:
            pass
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._save())
                else:
                    loop.run_until_complete(self._save())
            except Exception:
                pass
            return True
        return False
    
    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._data.values())
    
    def clear(self) -> None:
        self._data.clear()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._save())
            else:
                loop.run_until_complete(self._save())
        except Exception:
            pass


# Global storage instance
_storage: Optional[StorageBackend] = None
_storage_backend: str = "memory"


def get_storage() -> StorageBackend:
    """Get the current storage backend."""
    global _storage
    if _storage is None:
        _storage = InMemoryStorage()
    return _storage


def set_storage(storage: StorageBackend) -> None:
    """Set the storage backend."""
    global _storage
    _storage = storage


def init_storage(
    backend: str = "memory",
    file_path: str = "ghostapi_data.json",
    force: bool = False
) -> StorageBackend:
    """
    Initialize storage backend.
    
    Args:
        backend: Storage type ("memory", "file", "buffered", "async_file").
        file_path: Path for file storage.
        force: Force reinitialization even if already initialized.
    
    Returns:
        The initialized storage backend.
    """
    global _storage, _storage_backend
    
    if _storage is not None and not force:
        return _storage
    
    _storage_backend = backend
    
    if backend == "file":
        _storage = FileStorage(file_path)
    elif backend == "buffered":
        _storage = BufferedFileStorage(file_path)
    elif backend == "async_file":
        _storage = AsyncFileStorage(file_path)
    else:
        _storage = InMemoryStorage()
    
    return _storage
