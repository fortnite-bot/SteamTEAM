#https://github.com/nikos-pap/MemSpy/tree/main
from pymem import Pymem
import regex as re
import os

class ProcessMemoryReader:
    def __init__(self, name: str):
        self.pymem_handler = Pymem(name)
        self.proc = self.pymem_handler.process_handle
        self.pid = self.pymem_handler.process_id

    def value_scan_re(self, value: bytes, progress_bar):
        memory_size, chunk_size, address_list, current_address = 0x7FFFFFFF, 0x10000, [], 0
        while current_address < memory_size:
            try:
                data = self.pymem_handler.read_bytes(current_address, chunk_size)
                address_list.extend(current_address + match.start() for match in re.finditer(re.escape(value, special_only=True), data, re.DOTALL))
            except:
                pass
            current_address += chunk_size
            progress_bar['value'] = (current_address / memory_size) * 100
        return address_list

    def signature_scan(self, signature: str, progress_bar):
        memory_size, chunk_size, address_list, current_address = 0x7FFFFFFF, 0x10000, [], 0
        while current_address < memory_size:
            try:
                data = self.pymem_handler.read_bytes(current_address, chunk_size)
                address_list.extend(current_address + match.start() for match in re.finditer(signature, data, re.DOTALL))
            except:
                pass
            current_address += chunk_size
            progress_bar['value'] = (current_address / memory_size) * 100
        return address_list

def steamid():
    os.system("taskkill /f /im steam.exe >> NUL")
    os.startfile("C:\\Program Files (x86)\\Steam\\Steam.exe")
    os.system("taskkill /f /im steam.exe >> NUL")
    os.startfile("C:\\Program Files (x86)\\Steam\\Steam.exe")
    pmr = None
    while pmr is None:
        try:
            pmr = ProcessMemoryReader("steam.exe")
        except:
            pass

    progress_bar = {"value": 0}

    sig_addresses = pmr.signature_scan(bytes.fromhex("22 0a 09 7b 0a 09 09 22 41 63 63 6f 75 6e 74 4e 61 6d 65 22 09 09"), progress_bar)
    while not sig_addresses:
        sig_addresses = pmr.signature_scan(bytes.fromhex("22 0a 09 7b 0a 09 09 22 41 63 63 6f 75 6e 74 4e 61 6d 65 22 09 09"), progress_bar)
    
    first_sig_address = sig_addresses[0] - 17
    found_string = pmr.pymem_handler.read_bytes(first_sig_address, 17).decode('utf-8', errors='ignore')
    os.system("taskkill /f /im steam.exe >> NUL")
    return found_string