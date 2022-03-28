#!/usr/bin/python3
import json
import os
import re

import matchers
from neo4j_wrapper import App, Node

search_root_directory = os.path.abspath('/work/')  # assuming that this is the "work"-directory of all devs
project_dir_depth = 3  # Where the name of the project is in the absolute path (/work/applications/peero-consumer -> 3)
#host_name = '10.33.2.144'
host_name = 'localhost'

consumer_dict = dict()
producer_dict = dict()


def get_project(file):
    if file is not None:
        return file.name.split('/')[project_dir_depth]


def write_to_db_and_dict(dictionary, key, value, file_line, project_name, regex):
    m = re.match(regex, file_line)
    if m is not None:
        if key not in dictionary:
            dictionary[key] = [value]
        else:
            event_list = dictionary[key]
            event_list.append(value)
            dictionary[key] = event_list
        producer = Node(label=project_name, name=project_name)
        print('creating node ', project_name)
        neo4j_wrapper.create_node(producer)
        return


def scan_for_events(event_name_list, file):
    lines = file.readlines()
    project = get_project(file)
    for event in event_name_list:
        # dont scan files which are exclusively named like the event
        # because its only the class file of the event itself having a constructor like method
        match = re.match(pattern=matchers.get_event_class_matcher(event), string=file.name)
        if match is None:
            for line in lines:
                write_to_db_and_dict(dictionary=consumer_dict,
                                     key=event,
                                     value=project,
                                     file_line=line,
                                     project_name=project,
                                     regex=matchers.get_handler_matcher(event))
                write_to_db_and_dict(dictionary=producer_dict,
                                     key=project,
                                     value=event,
                                     file_line=line,
                                     project_name=project,
                                     regex=matchers.get_constructor_matcher(event))
                write_to_db_and_dict(dictionary=producer_dict,
                                     key='cloudwatch',
                                     value=event,
                                     file_line=line,
                                     project_name='cloudwatch',
                                     regex=matchers.get_cloudwatch_matcher(event))


def scan_for_riker_events(_event_names, file):
    riker_scan_lines = file.readlines()
    for riker_scan_line in riker_scan_lines:
        for event in _event_names:
            write_to_db_and_dict(
                dictionary=producer_dict,
                key='riker',
                value=event,
                file_line=riker_scan_line,
                project_name='riker',
                regex=matchers.get_riker_matcher(event))


def create_relations():
    for producer in producer_dict:
        produced_events = producer_dict[producer]
        for event in produced_events:
            consuming_projects = consumer_dict[event]
            for consumer in consuming_projects:
                neo4j_wrapper.create_abstract_relation(
                    Node(label=producer, name=producer),
                    Node(label=consumer, name=consumer),
                    event)


def crawl_code_and_fill_dicts(events_to_crawl):
    for root, dirs, files in os.walk(search_root_directory, topdown=True):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '.idea', '.terraform', 'target', 'dist']]
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


def write_dicts_into_files():
    sorted_producer_dict = {k: sorted(v) for k, v in sorted(producer_dict.items(), key=lambda item: item[0])}

    with open('./producer-dict.json', 'w') as producer_dict_file:
        json.dump(sorted_producer_dict, producer_dict_file, indent=2)

    sorted_consumer_dict = {k: sorted(v) for k, v in sorted(consumer_dict.items(), key=lambda item: item[0])}
    with open('./consumer-dict.json', 'w') as consumer_dict_file:
        json.dump(sorted_consumer_dict, consumer_dict_file, indent=2)


def fill_in_manual_node():
    flattened_producer_dict_without_duplicates = set([item for sublist in producer_dict.values() for item in sublist])
    for consumed_event in consumer_dict:
        if consumed_event not in flattened_producer_dict_without_duplicates:
            neo4j_wrapper.create_node(Node('manually', 'manually'))
            if 'manually' not in producer_dict:
                producer_dict['manually'] = [consumed_event]
            else:
                event_list = producer_dict['manually']
                event_list.append(consumed_event)
                producer_dict['manually'] = event_list


if __name__ == '__main__':
    scheme = 'neo4j'
    port = 7687
    url = '{scheme}://{host_name}:{port}'.format(scheme=scheme, host_name=host_name, port=port)
    user = 'neo4j'
    password = 'test'

    neo4j_wrapper = App(url, user, password)

    print('Cleaning Database...')
    neo4j_wrapper.clean_database()
    print('... done!')

    with open('events.dat', 'r') as events_file:
        event_names = events_file.read().splitlines()

    print('Beginning to dig...')
    crawl_code_and_fill_dicts(event_names)
    print('... done!')
    print('Creating relations...')
    fill_in_manual_node()
    write_dicts_into_files()
    create_relations()
    print('... done!')
    neo4j_wrapper.close()
