import copy
import networkx as nx

from Icarus_main.Classes.agent_class import *


def trip_routing(graph: nx.Graph, trip_start, trip_end):
    """
    routing the trip on the network
    :param graph:
    :param trip_start:
    :param trip_end:
    :return:
    """
    try:
        return nx.bidirectional_shortest_path(graph, trip_start, trip_end)
    except:
        return None


def route(trip: Route, graph: nx.Graph) -> Route:
    """
    return the route and update if the trip got rerouted
    :param trip:
    :param graph:
    :return:
    """
    if trip.route is None:
        new_trip = copy.deepcopy(trip) #deepcopy is extremely slow
        new_route = trip_routing(graph, trip.route[0], trip.route[-1])
        return new_trip
    else:
        return reroute(trip, graph)


def reroute(trip: Route, graph: nx.Graph) -> Route:
    new_route = trip_routing(graph, trip.route[0], trip.route[-1])
    if new_route == trip.route:
        trip.reroute = 0
        return copy.deepcopy(trip) #deepcopy is extremely slow
    else:
        new_trip = copy.deepcopy(trip)
        new_trip.route = new_route
        new_trip.reroute = 1
        return new_trip

