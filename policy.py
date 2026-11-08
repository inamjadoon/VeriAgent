"""Simple regex safety policy. Any finding blocks execution."""
import re

RULES = [
    (r"\brequests\b", "network: requests"),
    (r"\burllib\b", "network: urllib"),
    (r"\bsocket\b", "network: socket"),
    (r"\bhttp\.client\b", "network: http.client"),
    (r"\bsubprocess\b", "shell: subprocess"),
    (r"\bos\.system\b", "shell: os.system"),
    (r"\bos\.popen\b", "shell: os.popen"),
    (r"\bshutil\.rmtree\b", "destructive: shutil.rmtree"),
    (r"(?<![\w.])eval\s*\(", "dynamic code: eval("),
    (r"(?<![\w.])exec\s*\(", "dynamic code: exec("),
    (r"open\s*\(\s*['\"]/etc", "system file: open('/etc...')"),
    (r"\bos\.environ\b", "secrets: os.environ"),
    (r"__import__", "dynamic import: __import__"),
]


def scan(code: str) -> list[str]:
    return [reason for pattern, reason in RULES if re.search(pattern, code)]
