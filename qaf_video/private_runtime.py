"""Privacy defaults for a separate local inference process, never the web server."""
import ctypes
import ctypes.util
import errno
import os
import sys


def harden_local_runtime():
    # Set before ONNX Runtime / Hugging Face initialization, not after a session.
    for key,value in {
        'ORT_DISABLE_TELEMETRY':'1','HF_HUB_DISABLE_TELEMETRY':'1',
        'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','DO_NOT_TRACK':'1',
        'GRADIO_ANALYTICS_ENABLED':'False','TOKENIZERS_PARALLELISM':'false'
    }.items():os.environ[key]=value
    result={'telemetry_disabled_before_import':True,'models':'local_files_only',
            'network_guard':'environment_only'}
    if sys.platform.startswith('linux'):
        library=ctypes.util.find_library('seccomp')
        if not library:raise RuntimeError('Install libseccomp for isolated local voice inference on Linux')
        lib=ctypes.CDLL(library,use_errno=True)
        lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
        lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
        lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint];lib.seccomp_rule_add.restype=ctypes.c_int
        lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_load.restype=ctypes.c_int
        lib.seccomp_release.argtypes=[ctypes.c_void_p]
        context=lib.seccomp_init(0x7fff0000)  # SCMP_ACT_ALLOW
        if not context:raise RuntimeError('Could not create inference network policy')
        try:
            for name in [b'socket',b'connect',b'sendto',b'sendmsg',b'sendmmsg']:
                number=lib.seccomp_syscall_resolve_name(name)
                if number>=0 and lib.seccomp_rule_add(context,0x00050000|errno.EPERM,number,0)!=0:
                    raise RuntimeError('Could not restrict inference network calls')
            if lib.seccomp_load(context)!=0:raise RuntimeError('Could not load inference network policy')
        finally:lib.seccomp_release(context)
        result['network_guard']='linux_seccomp_denies_network_syscalls'
    return result
