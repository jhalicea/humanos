"""Bounded, read-only access to explicitly public-to-the-runtime source files.

This is a different scope from the user's workspace. It never makes a workspace,
Notebook, configuration, or arbitrary filesystem path readable to the model.
Offsets and page limits are UTF-8 byte counts; offsets must be character boundaries.
"""
import hashlib
import os
from pathlib import Path
import stat


ALLOWED_FILES = frozenset({
    'server.py', 'engine.py', 'notebook.py', 'runtime_info.py', 'permissions.py',
    'capabilities.py', 'audit.py', 'source_reader.py', 'file_manager.py',
    'README.md', 'REVIEW.md', 'AGENTS.md',
})
MAX_SOURCE_BYTES = 256 * 1024
MAX_PAGE_BYTES = 16000


class SourceReader:
    def __init__(self, root=None):
        # Do not resolve symlinks here: each component must pass O_NOFOLLOW below.
        self.root = Path(os.path.abspath(root if root is not None else Path(__file__).parent))

    def describe(self):
        return ('Read-only HumanOS source inspection in ' + str(self.root) + '. '
                'Allowed filenames: ' + ', '.join(sorted(ALLOWED_FILES)) + '. '
                'Notebook records, workspace files, configuration, credentials, and other '
                'paths are outside this tool. Pages contain at most 16000 UTF-8 bytes; '
                'offset and next_offset are byte offsets at character boundaries. '
                'Files larger than 256 KiB cannot be inspected with this tool.')

    def _open_root(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(self.root.anchor, flags)
        try:
            for component in self.root.parts[1:]:
                following = os.open(component, flags, dir_fd=fd)
                os.close(fd)
                fd = following
            return fd
        except BaseException:
            os.close(fd)
            raise

    def read(self, path='server.py', offset=0, limit=MAX_PAGE_BYTES):
        if not isinstance(path, str) or path not in ALLOWED_FILES:
            raise PermissionError('Source path is not an allowlisted HumanOS filename')
        if type(offset) is not int or offset < 0:
            raise ValueError('Source offset must be a non-negative UTF-8 byte offset')
        if type(limit) is not int or not 4 <= limit <= MAX_PAGE_BYTES:
            raise ValueError('Source page limit must be between 4 and 16000 UTF-8 bytes')

        root_fd = self._open_root()
        try:
            # NONBLOCK allows rejecting special files without blocking on FIFO open.
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd)
        finally:
            os.close(root_fd)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise PermissionError('Source must be a regular file with one hard link')
            if before.st_size > MAX_SOURCE_BYTES:
                raise ValueError('Source exceeds the 256 KiB inspection limit')
            chunks, length = [], 0
            while length <= MAX_SOURCE_BYTES:
                chunk = os.read(fd, min(65536, MAX_SOURCE_BYTES + 1 - length))
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
            if length > MAX_SOURCE_BYTES:
                raise ValueError('Source exceeds the 256 KiB inspection limit')
            after = os.fstat(fd)
            fingerprint = lambda info: (info.st_dev, info.st_ino, info.st_size,
                                         info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)
            if fingerprint(before) != fingerprint(after) or length != after.st_size:
                raise RuntimeError('Source changed while being read; retry inspection')
            content = b''.join(chunks)
        finally:
            os.close(fd)

        # Strict decoding rejects a binary or malformed file masquerading as source.
        content.decode('utf-8')
        if offset > len(content):
            raise ValueError('Source offset is beyond the end of the file')
        if offset < len(content) and content[offset] & 0xC0 == 0x80:
            raise ValueError('Source offset splits a UTF-8 character')
        end = min(offset + limit, len(content))
        while end < len(content) and content[end] & 0xC0 == 0x80:
            end -= 1
        truncated = end < len(content)
        return {'source': str(self.root / path), 'path': path,
                'text': content[offset:end].decode('utf-8'),
                'sha256': hashlib.sha256(content).hexdigest(),
                'truncated': truncated, 'next_offset': end if truncated else None,
                'total_bytes': len(content)}
