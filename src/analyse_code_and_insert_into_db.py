#!/usr/bin/python3

# Alternative script to create events as nodes instead of edges

import os
import re

from neo4j_wrapper import App, Node
import matchers

search_root_directory = os.path.abspath('../../')  # assuming that this is the "work"-directory of all devs


def get_project(file):
    if file is not None:
        return file.split('/')[4]


def write_to_db_if_subscriber(event, file, line):
    handler_matcher = re.compile(r'^\s*(public|protected).*void.*\((final )?' + event + r' .*$')
    m = re.match(handler_matcher, line)
    if m is not None:
        project = get_project(file)
        print('creating pubsub node: ', project)
        subscriber = Node(project, 'pubsub')
        neo4j_wrapper.create_node(subscriber)
        event = Node(event)
        neo4j_wrapper.create_relation(event, subscriber, 'subscribes')


def write_to_db_if_producer(event, file, line):
    constructor_matcher = re.compile(r'^.*(new\s*' + event + r'\(|' + event + r'(\.[a-zA-Z]*)\().*$')
    m = re.match(constructor_matcher, line)
    if m is not None:
        project = get_project(file)
        print('creating pubsub node: ', project)
        producer = Node(project, 'pubsub')
        neo4j_wrapper.create_node(producer)
        event = Node(event)
        neo4j_wrapper.create_relation(producer, event, 'produces')
        return


def write_to_db_if_cloudwatch_event(event, line):
    cloudwatch_matcher = re.compile(r'^\s*(message_type|event_type)\s*=\s*' + event + r'.*$')
    m = re.match(cloudwatch_matcher, line)
    if m is not None:
        print('creating cloudwatch node')
        node = Node('cloudwatch', 'pubsub')
        neo4j_wrapper.create_node(node)
        event = Node(event)
        neo4j_wrapper.create_relation(node, event, 'produces')
        return


def write_to_db_if_riker_event(event, file_line):
    riker_matcher = re.compile(r'^\s*' + event + r':\s*{{.*$')
    m = re.match(riker_matcher, file_line)
    if m is not None:
        print('creating riker node')
        node = Node('riker', 'pubsub')
        neo4j_wrapper.create_node(node)
        event = Node(event)
        neo4j_wrapper.create_relation(node, event, 'produces')
        return


def scan_for_events(event_name_list, file):
    lines = file.readlines()
    for line in lines:
        for event in event_name_list:
            # dont scan files which are exclusively named like the event
            # because its only the class file of the event itself having a constructor like method
            event_class_matcher = re.compile(r'^.*' + event + r'.java$')
            if re.match(pattern=event_class_matcher, string=file.name) is None:
                write_to_db_if_subscriber(event=event, file=file.name, line=line)
                write_to_db_if_producer(event=event, file=file.name, line=line)
                write_to_db_if_cloudwatch_event(event=event, line=line)


def scan_for_riker_events(_event_names, file):
    riker_scan_lines = file.readlines()
    for riker_scan_line in riker_scan_lines:
        for event in _event_names:
            write_to_db_if_riker_event(event, riker_scan_line)


def crawl_code_and_fill_db(events_to_crawl):
    for root, dirs, files in os.walk(search_root_directory):
        for file_name in files:
            file_path = root + '/' + file_name
            if re.match(pattern=matchers.whitelist_file_matcher, string=file_name):
                if re.match(pattern=matchers.testclass_matcher, string=file_path) is None \
                        and re.match(pattern=matchers.integrationtest_matcher, string=file_path) is None \
                        and re.match(pattern=matchers.e2etest_matcher, string=file_path) is None:
                    with open(file_path, 'r') as f:
                        scan_for_events(events_to_crawl, f)
            elif re.match(pattern=matchers.riker_file_matcher, string=file_path) is not None:
                with open(file_path, 'r') as f:
                    scan_for_riker_events(events_to_crawl, f)


if __name__ == '__main__':
    scheme = 'neo4j'
    # host_name = '10.33.2.210'
    host_name = 'localhost'
    port = 7687
    url = '{scheme}://{host_name}:{port}'.format(scheme=scheme, host_name=host_name, port=port)
    user = 'neo4j'
    password = 'test'

    neo4j_wrapper = App(url, user, password)

    neo4j_wrapper.clean_database()

    with open('events.dat', 'r') as events_file:
        event_names = events_file.read().splitlines()

    for event_name in event_names:
        neo4j_wrapper.create_node(Node(event_name, 'event'))

    crawl_code_and_fill_db(event_names)

    neo4j_wrapper.close()
