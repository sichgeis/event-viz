#!/usr/bin/python3

from neo4j_wrapper import App, Node

host_name = 'localhost'


event_names = [
    "UpdatedMasterData"
]

apps = [
    "customer",
    "shop",
    "billing",
    "bonus",
    "warehouse"
]

producer_dict = {
    "customer": [
        "CustomerCreated",
        "UpdatedCustomerMasterData",
        "CustomerDeleted",
    ],
    "shop": [
        "PurchaseReceived",
        "PurchaseCanceled",
    ],
    "billing": [
        "YearlyBillSend"
    ],
    "bonus": [
        "CustomerBonusUpdated"
    ],
    "warehouse": [
        "ItemOutOfStock",
        "ItemShipped"
    ]
}

consumer_dict = {
    "CustomerCreated": [
        "billing",
        "shop"
    ],
    "UpdatedCustomerMasterData": [
        "billing",
        "shop"
    ],
    "CustomerDeleted": [
        "billing",
        "shop"
    ],
    "PurchaseReceived": [
        "billing",
        "bonus"
    ],
    "PurchaseCanceled": [
        "billing",
        "bonus"
    ],
    "YearlyBillSend": [
        "customer"
    ],
    "CustomerBonusUpdated": [
        "shop",
        "billing"
    ],
    "ItemOutOfStock": [
        "shop"
    ],
    "ItemShipped": [
        "billing",
        "bonus"
    ]
}


def create_app_nodes():
    global system

    for system in apps:
        new_node = Node(label=system, name=system)
        neo4j_wrapper.create_node(new_node)


def create_relations():
    global producer_dict
    global consumer_dict

    for producer in producer_dict:
        produced_events = producer_dict[producer]
        for event in produced_events:
            consuming_projects = consumer_dict[event]
            for consumer in consuming_projects:
                neo4j_wrapper.create_abstract_relation(
                    Node(label=producer, name=producer),
                    Node(label=consumer, name=consumer),
                    event)


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

    print('Creating app nodes...')
    create_app_nodes()
    print('... done!')

    print('Creating relations...')
    create_relations()
    print('... done!')

    neo4j_wrapper.close()
