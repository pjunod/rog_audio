"""Observe native pw-cat raw-mode capability before guarded PCM startup."""
import re
import resource
import subprocess
import tempfile

MAX_HELP_BYTES = 65536
HELP_SECONDS = 2


def raw_mode_options(env):
    """Old pw-cat treats '-' as raw; newer versions advertise --raw."""
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_HELP_BYTES, MAX_HELP_BYTES))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(['pw-cat', '--help'], stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.DEVNULL, env=dict(env, LC_ALL='C'),
                timeout=HELP_SECONDS, preexec_fn=limits)
            output.seek(0)
            help_text = output.read(MAX_HELP_BYTES + 1)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('pw-cat-capabilities-unavailable') from exc
    if (result.returncode != 0 or not 0 < len(help_text) <= MAX_HELP_BYTES or
            any(option not in help_text for option in (b'--playback', b'--record', b'--format'))):
        raise ValueError('pw-cat-capabilities-unavailable')
    return ['--raw'] if re.search(rb'(?m)^\s*(?:-\w,?\s+)?--raw(?=[\s,=]|$)', help_text) else []
