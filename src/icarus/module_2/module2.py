# -*- coding: utf-8 -*-
"""
Created on Sun May 22 17:52:02 2022

@author: ruili
"""
import pandas as pd
import copy
import networkx as nx
import multiprocessing as mp
from itertools import product
import pickle
import time

# this section only for code runs on AGAVE
# import sys
# sys.path.append('/home/ruili11/Icarus_paper_two/Icarus_rui')


from prepare.prepare_network import get_graph_network, get_link_weight
import export_map.export_link_flow as link_flow
import Classes.class_reader as class_reader
from Paper_Two.prepare_dt import *
import prepare.prepare_mrt as prepare_mrt
from Classes.classes import Link, Link_Env
from Processer.postprocessers import calculate_route_mrt, calculate_route_mrt_no_change
from Paper_Two.prepare_new_temp import *


def __route(_graph, start_lc, end_lc):
    try:
        return nx.bidirectional_dijkstra(_graph, start_lc, end_lc)[-1]
    except:
        return None


def generate_network(link_attributs, weight, db):
    nodes = class_reader.read_link_nodes(db)[1]
    return get_graph_network(nodes, link_attributs, weight)


def _update_OG_route(inp):
    route_obj = inp[0]
    new_graph_obj = inp[1][0]
    og_graph_obj = inp[1][1]

    if len(route_obj.route) > 1:
        _new_route = __route(new_graph_obj, route_obj.route[0], route_obj.route[-1])
        if _new_route != route_obj.route:
            route_obj.route = _new_route
    else:
        route_obj.route = None
        pass
    if route_obj.route is not None:
        route_obj.mrt_exp = 0
        route_obj.length = nx.classes.function.path_weight(og_graph_obj, route_obj.route, weight="weight")
        return route_obj
    else:
        pass


def _update_route(routes_list, new_graph, og_graph, pool_num: int = 6):
    # read network and build network
    _df_s = [(_, (new_graph, og_graph)) for _ in routes_list if _ is not None]
    print('multi_processing start')
    # og_routes = [_update_OG_route(_, graph) for _ in s0]
    start = time.time()
    p = mp.Pool(pool_num)
    results = p.map(_update_OG_route, _df_s)
    print('finish')
    temp = [x for x in results if x is not None]
    p.close()
    print(time.time() - start)
    return temp


def _read_OG(_db_url, og_graph, pool_num: int = 6):
    s0 = class_reader.route_reader(_db_url, 's0')
    # read network and build network
    return _update_route(s0, og_graph, og_graph, pool_num)


def _select_hot_corridors(linkflow_df, cool_list, number_flow):
    return list(linkflow_df.query('usage >= @number_flow and index !=@cool_list').index)


def _select_corridor_length(link_df, select_corridor):
    return sum(link_df.query('link_id == @select_corridor').length)


def create_scenario(link_flow_df, cool_corridor_list):
    hot_corridors_scenario = []
    # picked scenarios manually:
    _scenairo_link_flow = [1,
                           50]  # [1,50,70,100,125,150,175,200,250,500,530,610,740,990,1140,1350,1710,1860,2150,2310,2700,3950]
    for i in _scenairo_link_flow:
        corr_select = _select_hot_corridors(link_flow_df, cool_corridor_list, i)
        hot_corridors_scenario.append({'usage_min': i,
                                       'length': _select_corridor_length(link_used_df, corr_select) / 1000,
                                       'link_list': corr_select})
        # scenarios = pd.DataFrame(hot_corridors_scenario).groupby('length').agg({'usage_min':'min'})

        scenario_list = list(pd.DataFrame(hot_corridors_scenario).groupby('length').agg({'usage_min': 'max'}).usage_min)
    return scenario_list, hot_corridors_scenario


# def return_cool_env(_db, cool_ratio_no: float = 0.05):
#     links, nodes = class_reader.read_link_nodes(_db)
#     print('load')
#     return prepare_mrt.find_cool_corridor(links, cool_ratio = cool_ratio_no )

def return_cool_env(link_db, temp_db, cool_ratio_no: float = 0.05):
    links, nodes = class_reader.read_link_nodes(link_db)
    print('load')
    return prepare_mrt.find_cool_corridor(links, temp_db=temp_db, cool_ratio=cool_ratio_no)


def export_result_to_tb(folder, hot_corridors_scenario):
    temp_dt = []
    for _ in hot_corridors_scenario:
        _ = hot_corridors_scenario[0]
        _sce = pd.read_pickle(f'{folder}\sce10_{_["usage_min"]}.pickle')
        _delta_temp_og = [_sce['env'][_][0] - s0[_].mrt_exp for _ in range(len(s0))]
        _delta_temp_rt = [round((_sce['env_re'][_][0] - s0[_].mrt_exp), 2) for _ in range(len(s0))]
        _cool_temp_og = sum(1 for _ in _delta_temp_og if _ < 0)
        _hot_temp_og = sum(1 for _ in _delta_temp_og if _ > 0)
        _cool_temp_rt = sum(1 for _ in _delta_temp_rt if _ < 0)
        _hot_temp_rt = sum(1 for _ in _delta_temp_rt if _ > 0)
        _distance_temp_rt = [round((_sce['env_re'][_][1] - s0[_].length), 2) for _ in range(len(s0))]
        temp_dt.append({'sce': _["usage_min"],
                        'n_cool_og_0.1': len(_cool_temp_og), 'n_hot_og_0.1': len(_hot_temp_og),
                        'n_cool_rt_0.1': len(_cool_temp_rt), 'n_hot_rt_0.1': len(_hot_temp_rt),
                        't_cool_og_0.1': sum(_cool_temp_og) / len(_cool_temp_og),
                        't_hot_og_0.1': sum(_hot_temp_og) / len(_hot_temp_og),
                        't_cool_rt_0.1': sum(_cool_temp_rt) / len(_cool_temp_rt),
                        't_hot_rt_0.1': sum(_hot_temp_rt) / len(_hot_temp_rt),
                        't_change_og_0.1': sum(_delta_temp_og) / len(_delta_temp_og),
                        't_change_rt_0.1': sum(_delta_temp_rt) / len(_delta_temp_rt)
                        })
    pd.DataFrame(temp_dt).to_csv(r'G:\Work\2022 Icarus\Icarus project\2.Changing_env\data\new_mrt\result1.csv',
                                 index=False)


def change_hot_corridors_mrt(mrt_dict, hot_corridors_list, all_links_dict, cool_corridors_target_temp):
    """

    :param mrt_dict: a dictionary of MRT temperature , no LCZ info
    :param hot_corridors_list: just a list of hot corridors.
    :param all_links_dict: link obj list
    :param cool_corridors_target_temp:
    :return:
    """
    hot_corridors_mrt_list = {all_links_dict[_].mrt_id: all_links_dict[_].LCZ for _ in hot_corridors_list if
                              _ in all_links_dict}
    temp_mrt = {
        i: cool_corridors_target_temp[hot_corridors_mrt_list[i]] if i in hot_corridors_mrt_list else copy.deepcopy(
            mrt_dict[i]) for i in mrt_dict}
    return temp_mrt


def get_hot_corridors_length(cool_corridor_list, hot_corridors_list, link_dict):
    _left_links = set(set(hot_corridors_list) - set(cool_corridor_list))
    return int(sum(link_dict[_].length for _ in _left_links))


def update_result(og_rt, re_rt):
    _update_list = [og_rt[_] if re_rt[_][0] > og_rt[_][0] else re_rt[_] for _ in range(len(og_rt))]
    # _update_list = [1 for _ in range(len(og_rt)) if re_rt[_][0]> og_rt[_][0] ]

    return _update_list


if __name__ is '__main__':
    print('enter_code')
    _folder = r'C:\test_codes_delete_later\re_run_mrt'  # previously r'C:\test_codes_delete_later\sqlite\db\'
    db = f'{_folder}\pythonsqlite.db'  # in version 2
    db2 = f'{_folder}\db_test.db'  # in version 2
    _out_foler = r'C:\test_codes_delete_later\re_run_mrt\result'
    pool_num = 2
    _cool_level = [0.1, 0.2, 0.5]

    all_links_dict = read_all_link_attr(url=db)
    # read routes
    og_graph = generate_network(all_links_dict, get_link_weight(all_links_dict), db)

    s0 = _read_OG(db2, og_graph, pool_num)
    # with open(f'{_out_foler}\og.pickle','wb') as output_file:
    #     #pickle.dump({'sce':_["usage_min"], 'env':R1}, output_file)
    #     pickle.dump({'env':R1, 'env_re':R2}, output_file)
    # output_file.close()
    mrt_dict = class_reader.read_mrt(db2)

    [calculate_route_mrt_no_change(_, all_links_dict, mrt_dict) for _ in s0]
# #     # get cool and warm corridors and change the network weight
# #     # #2. get cool list and cool environment
#     for __ in _cool_level:
#         cool_corridors_target_temp, cool_corridor_list = return_cool_env(db, db2, __)
# #     # #1. you need to get link flow.and link length
#         link_used_df, link_flow_df = link_flow.get_corridor_info(s0, db)
#         scenario_list, hot_corridors_scenario = create_scenario(link_flow_df,cool_corridor_list)
# #     #3. get hot corridor list under different scenarios
# #     """create a list of scenarios"""
#         for _ in hot_corridors_scenario:

#             new_mrt_dict = change_hot_corridors_mrt(mrt_dict, _['link_list'], all_links_dict, cool_corridors_target_temp)
#             _hot_corridors_length = get_hot_corridors_length(cool_corridor_list, _['link_list'], all_links_dict )
#             _dt = copy.deepcopy(s0)
#             R1 = [calculate_route_mrt_no_change(_, all_links_dict, new_mrt_dict) for _ in _dt]
#             #generate new graph and run
#             new_graph = generate_network(all_links_dict, get_link_weight(all_links_dict, new_mrt_dict),db)
#             _dt1 = _update_route(_dt, new_graph, og_graph, pool_num)
#             _R2 = [calculate_route_mrt_no_change(_, all_links_dict, new_mrt_dict) for _ in _dt1]
#             R2 = update_result(R1, _R2)
#             with open(f'{_out_foler}\sce{int(__*100)}_{_["usage_min"]}.pickle','wb') as output_file:
#                 #pickle.dump({'sce':_["usage_min"], 'env':R1}, output_file)
#                 pickle.dump({'sce':_["usage_min"], 'cool_ratio':__,'corridor_length': _hot_corridors_length, 'env':R1, 'env_re':R2}, output_file)
#             output_file.close()


