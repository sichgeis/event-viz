import re

whitelist_file_matcher = re.compile(r'^\S*\.(java|tf)$')
testclass_matcher = re.compile(r'^.*(Test|TEST|test).*$')
integrationtest_matcher = re.compile(r'^.*IT.*$')
e2etest_matcher = re.compile(r'^.*[Ee]2[Ee].*$')
riker_file_matcher = re.compile(r'^.*commander-riker.*event_templates.py$')


def get_constructor_matcher(event):
    return re.compile(r'^.*(new\s*' + event + r'\(|' + event + r'(\.[a-zA-Z]*)\().*$')


def get_cloudwatch_matcher(event):
    return re.compile(r'^\s*(message_type|event_type)\s*=\s*"' + event + r'".*$')


def get_riker_matcher(event):
    return re.compile(r'^\s*\'' + event + r'\'\s*:\s*{.*$')


def get_event_class_matcher(event):
    return re.compile(r'^.*' + event + r'\.java$')


def get_handler_matcher(event):
    return re.compile(r'^\s*(public|protected).*void.*\((final )?' + event + r' .*$')
