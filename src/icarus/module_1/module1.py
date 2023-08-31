"""
This is the script for Icarus paper one.
Routing trips and calculate heat exposure (Mean Radiant Temperature, Air Temperature, and Web-bolb globe temperature.
1. connect to environment database (project) and build new result database
if database not exist, reminder user go to the preprocessing step to initiate the project
2. load trips from the initialized database
3. identify start and end location on the transportation network
4. routing trips (the shortest distance path)
5. load temperature profile and calculating heat exposure
6. store result into E_Trip and E_Trip_plan table in the result database
"""
import os
from rtree import index
import sys

module_path = os.path.abspath(os.path.join(r"D:\Icarus_RL"))
if module_path not in sys.path:
    sys.path.append(module_path)
from src.icarus.project.project_class import *
from src.icarus.util.sqlite_db_general_func import *
from Icarus_main.utils.calculate_exposure import *


def load_network_as_graph(db_conn: sqlite3.Connection, node_table: str = 'L_Node',
                          link_table: str = 'L_Link', project_crs: int = 4326) -> networkx.Graph:
    """

    :param db_conn:
    :param node_table:
    :param link_table:
    :param project_crs:
    :return:
    """
    _nodes_data = pd.read_sql_query(f"SELECT * FROM {node_table}", db_conn)
    _links_data = pd.read_sql_query(f"SELECT * FROM {link_table}", db_conn)
    g = networkx.Graph()
    g.graph["crs"] = f'epsg:{project_crs}'
    _nodes_data.apply(lambda x: g.add_node(int(x['node_id']), **{'x': x['x'], 'y': x['y']}), axis=1)
    _links_data.apply(lambda x: g.add_edge(int(x['node1']), int(x['node2']), weight=x['length']), axis=1)
    return g


def load_travel_plan(db_conn: sqlite3.Connection, activity_table: str = 'P_Activity',
                     trip_table: str = 'P_Trip', parcel_location: str = 'L_Parcel') -> pd.DataFrame:
    """
    return active trips' travel plan with start and end APN
    :param db_conn:
    :param activity_table:
    :param trip_table:
    :param parcel_location:
    :return:
    """
    query = f"""
    SELECT {trip_table}.*,
    (
        SELECT {parcel_location}.x
        FROM {parcel_location}
        JOIN {activity_table} 
        ON {parcel_location}.apn = {activity_table}.apn 
        WHERE {trip_table}.hhid = {activity_table}.hhid
        AND {trip_table}.pnum = {activity_table}.pnum
        AND {trip_table}.personTripNumber = {activity_table}.personActNumber
    ) AS x1,
    (
        SELECT {parcel_location}.y
        FROM {parcel_location}
        JOIN {activity_table} 
        ON {parcel_location}.apn = {activity_table}.apn 
        WHERE {trip_table}.hhid = {activity_table}.hhid
        AND {trip_table}.pnum = {activity_table}.pnum
        AND {trip_table}.personTripNumber = {activity_table}.personActNumber
    ) AS y1,
    (
        SELECT {parcel_location}.x
        FROM {parcel_location}
        JOIN {activity_table} 
        ON {parcel_location}.apn = {activity_table}.apn 
        WHERE {trip_table}.hhid = {activity_table}.hhid
        AND {trip_table}.pnum = {activity_table}.pnum
        AND {trip_table}.personTripNumber = {activity_table}.personActNumber+1
    ) AS x2,
    (
        SELECT {parcel_location}.y
        FROM {parcel_location}
        JOIN {activity_table} 
        ON {parcel_location}.apn = {activity_table}.apn 
        WHERE {trip_table}.hhid = {activity_table}.hhid
        AND {trip_table}.pnum = {activity_table}.pnum
        AND {trip_table}.personTripNumber = {activity_table}.personActNumber+1
    ) AS y2
    FROM {trip_table}
    WHERE {trip_table}.mode IN ('walk', 'bike')
    LIMIT 500;
    """
    return pd.read_sql_query(query, db_conn)


def network_nodes_rtree(nodes: dict) -> index.Index:
    """

    :param nodes:
    :return:
    """
    idx = index.Index()
    [idx.insert(int(_), (nodes[_]['x'], nodes[_]['y'], nodes[_]['x'], nodes[_]['y'])) for _ in nodes.keys()]
    return idx


def get_trip_OD_nodes(network_nodes_rtree: index.Index, travel_plan_with_od: pd.DataFrame) -> pd.DataFrame:
    """
    [NOTE: this function is sensitive to data structure]
    :param network_nodes_rtree:
    :param travel_plan_with_od:
    :return:
    """
    travel_plan_with_od['start_node'] = travel_plan_with_od.apply(
        lambda x: next(network_nodes_rtree.nearest((x['x1'], x['y1'], x['x1'], x['y1']), 1)), axis=1)
    travel_plan_with_od['end_node'] = travel_plan_with_od.apply(
        lambda x: next(network_nodes_rtree.nearest((x['x2'], x['y2'], x['x2'], x['y2']), 1)), axis=1)
    return travel_plan_with_od


def route_trips(network_graph: networkx.Graph, start_node: int, end_node: int):
    """
    find trip route in network
    :param network_graph:
    :param start_node:
    :param end_node:
    :return:
    """
    try:
        return networkx.bidirectional_dijkstra(network_graph, start_node, end_node)[-1]
    except:
        return None


def get_trips_route(source_db_conn: sqlite3.Connection) -> pd.DataFrame:
    """
    use the data from preprocessing to find the travel plan and trip route
    :param source_db_conn:
    :return:
    """
    print('retrieve network')
    network = load_network_as_graph(source_db_conn)
    # load personal travel schedule (active trips)
    print('network retrieved')
    print('retrieve travel plan')
    active_trip_plan = load_travel_plan(source_db_conn).dropna()
    # get the closest point to each APN
    get_trip_OD_nodes(network_nodes_rtree=network_nodes_rtree(nodes=network.nodes),
                      travel_plan_with_od=active_trip_plan)
    print('travel plan retrieved')
    # route people's travel
    print('routing active trips')
    active_trip_plan['route'] = active_trip_plan.apply(lambda x: route_trips(network, x['start_node'], x['end_node']),
                                                       axis=1)
    print('finished routing')
    return active_trip_plan.drop(columns=['x1', 'y1', 'x2', 'y2'])


def get_temp_dict(db_cursor: sqlite3.Cursor, table_name: str) -> dict:
    """

    :param db_cursor:
    :param table_name:
    :return:
    """
    db_cursor.execute(f"SELECT * FROM {table_name}")
    data = db_cursor.fetchall()
    return data


def main():
    print('please connect to an existing database location')
    project_data = get_project_database()
    # check project and give options
    print('please provide a new database location for result')
    result_project = get_project_database()

    # use the existing information to identify the trip route
    project_data.connect()
    active_trip_plan = get_trips_route(project_data.db_conn)
    network = load_network_as_graph(project_data.db_conn)
    result_project.connect()
    _column_keep = ['hhid', 'pnum', 'personTripNumber', 'abmStart', 'abmEnd', 'mode', 'start_node', 'end_node']
    add_dataframe_to_database(conn=result_project.db_conn, data_frame=active_trip_plan[_column_keep],
                              table_name='P_Trip_plan',
                              primary_keys=['hhid', 'pnum', 'personTripNumber'])
    # calculate trip exposure
    # 1. load network temperature as dictionary
    print('calculating exposure')
    _mrt_temp = {_t[:2]: {_: _t[_-5] for _ in range(7, 21)} for _t in get_temp_dict(project_data.db_cursor,
                                                                                    table_name='E_Link_mrt')}
    _air_temp = {_: {'tmin': min(_mrt_temp[_].values()), 'tmax': 480} for _ in _mrt_temp}
    routes = active_trip_plan.apply(lambda x: Route(hhid=x['hhid'], pnum=x['pnum'], personTripNumber=x['personTripNumber'],
                                               mode=x['mode'], route=x['route'], abmStart=x['abmStart'],
                                               abmEnd=x['abmEnd']), axis=1).to_list()
    [calculate_exposure(_, network, _air_temp, _mrt_temp) for _ in routes]
    add_dataframe_to_database(conn=result_project.db_conn, data_frame=pd.DataFrame(routes).drop('route', axis=1),
                              table_name='E_Trip',
                              primary_keys=['hhid', 'pnum', 'personTripNumber'])
    result_project.close_connection()
    project_data.close_connection()


if __name__ == "__main__":
    main()
