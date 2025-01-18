# TIK_Project
LZ77 and CRC32
This project is a simple file compressor and decompressor based on LZ77, with a built-in CRC32 check to catch errors. It scans for repeating sequences, stores them as (offset, length, symbol) tokens, and then appends a 4-byte CRC32. That way, when you decompress, the program can verify everything is still correct. It's written in Python.
