#!/usr/bin/python3
import os
import re

search_root_directory = os.path.abspath('../../')  # assuming that this is the "work"-directory of all devs
java_file_matcher = re.compile(r'^\S*.java$')
package_matcher = re.compile(r'^package (.*);\\n$')
events_blacklist = ["T", "TestEvent", "DomainEvent", "Message", "InputStream", "DummyEvent", "EventProcessorHealthCheck"]


def add_event(event_line):
    event_matcher = re.compile(r'^\s*(public|protected).*void.*(handle|processEvent).*\((final )?(\S*).*$')
    m = re.search(event_matcher, event_line)
    if m is not None and m[4] not in events_blacklist:
        # print(m[4])
        events.add(m[4])


def scan_for_events(file_to_scan):
    lines = file_to_scan.readlines()
    for line in lines:
        add_event(line)


if __name__ == "__main__":
    events = set()
    data = {}

    for root, dirs, files in os.walk(search_root_directory):
        for name in files:
            if re.match(pattern=java_file_matcher, string=name):
                file = root + "/" + name
                with open(file, 'r') as f:
                    scan_for_events(f)

    with open('events.dat', 'w') as outfile:
        event_list = list(events)
        event_list.sort()
        for event in event_list:
            outfile.write(event + "\n")
