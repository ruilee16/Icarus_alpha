import pandas as pd
from pylab import *
from dataclasses import dataclass
from typing import List
import networkx
import functools
from Icarus_main.utils.utilities import update_dataclass


@dataclass
class Route:
    hhid: int = 0
    pnum: int = 0
    personTripNumber: int = 0
    mode: str = 'walk'
    route: List[int] = 0
    abmStart: int = 0
    abmEnd: int = 0
    length: int = 0
    mrt_exp: int = 0
    daymet_exp: int = 0
    wbgt_exp: int = 0


def calculate_NWB(trip, RH):
    """

    :param trip:
    :param RH: relative humidity.
    :return:
    """
    NWB = -5.806 + 0.672 * trip.daymet_exp - 0.006 * trip.daymet_exp ** 2 + \
          (0.061 + 0.004 * trip.daymet_exp + 99 * 10 ** (-6) * trip.daymet_exp ** 2) * RH * 100 - \
          (33 * 10 ** (-6) + 5 * 10 ** (-6) * trip.daymet_exp + 1 * 10 ** (-7) * trip.daymet_exp ** 2) * (RH * 100 ** 2)
    return NWB


def calculate_NWB_1(trip, RH):
    NWB = trip.daymet_exp * math.atan(0.151977 * ((RH * 100 + 8.313659) ** (1 / 2))) + math.atan(
        (trip.daymet_exp + RH * 100)) - math.atan(RH * 100 - 1.676331) + 0.00391838 * (
                  (RH * 100) ** (3 / 2)) * math.atan(
        0.023101 * RH * 100) - 4.686035  # Stull 2011 method. Calculation checked
    return NWB


def calculate_GT(trip, Va):
    # solve Ts_bar: (Ts_bar + 273.15)^4+p[3](Ts_bar+273.15)+P[4]=0
    '''
    alpha = (0.24 + 2.08 * (Va ** 0.5) + 1.14 * (Va ** 0.667)) * (10 ** 8)
    if math.isnan(trip.mrt_exp):
        trip.mrt_exp = 60
    belta = -alpha * 273.15 - alpha * trip.daymet_exp - (trip.mrt_exp + 273.15) ** 4
    '''
    p_3 = 6 * Va ** 0.466 * 10 ** 8
    p_4 = -(trip.daymet_exp + 273.15) * 10 ** 8 * 6 * Va ** 0.466 - (trip.mrt_exp + 273.15) ** 4
    # print([1, 0, 0, p_3, p_4])
    r = roots([1, 0, 0, p_3, p_4])
    # print(r)
    Ts_bar = r[(r.imag == 0) & (r.real >= 0)].real.min() - 273.15
    mrt = ((Ts_bar + 273.15) ** 4 + 6 * Va ** 0.466 * (Ts_bar - trip.daymet_exp) * 10 ** 8) ** 0.25 - 273.15
    # print(f'{trip.mrt_exp},{mrt}')
    GT = (Ts_bar - 0.725 + 0.369 * trip.daymet_exp) / 1.345
    return GT


def calculate_GT_1(trip, Va):
    """
    solve Ts_bar: (Ts_bar + 273.15)^4+p[3](Ts_bar+273.15)+P[4]=0
    alpha = (0.24 + 2.08 * (Va ** 0.5) + 1.14 * (Va ** 0.667)) * (10 ** 8)
    if math.isnan(trip.mrt_exp):
        trip.mrt_exp = 60
    belta = -alpha * 273.15 - alpha * trip.daymet_exp - (trip.mrt_exp + 273.15) ** 4
    :param trip:
    :param Va:
    :return:
    """
    p_3 = (0.24 + 2.08 * Va ** 0.5 + 1.14 * Va ** 0.667) * 10 ** 8
    p_4 = -(trip.daymet_exp + 273.15) * (0.24 + 2.08 * Va ** 0.5 + 1.14 * Va ** 0.667) * 10 ** 8 - (
            trip.mrt_exp + 273.15) ** 4
    r = roots([1, 0, 0, p_3, p_4])
    Ts_bar = r[(r.imag == 0) & (r.real >= 0)].real.min() - 273.15
    mrt = ((Ts_bar + 273.15) ** 4 + (0.24 + 2.08 * Va ** 0.5 + 1.14 * Va ** 0.667) * 10 ** 8 * (
            Ts_bar - trip.daymet_exp)) ** 0.25 - 273.15
    GT = (Ts_bar - 0.725 + 0.369 * trip.daymet_exp) / 1.345
    return GT


def Cal_WBGT(trip, RH: float = 0.2, Va: float = 3.2, outdoor: bool = True):
    '''
    Calculate WBGT using Vanos et al., 2021, Skull 2011, and Dimiceli & Piltz n.d. method.

    :param trip:
    :param RH: Relative Humidity (assume to be 20% in June @ Phoenix)
    :param Va:
    :param outdoor:
    :return:

    WBGT calculation: for outdoors with direct sun exposure:
        WBGT = 0.7*NWB + 0.2*Temp_globe + 0.1*Temp_air
    for indoors and outdoors without direct sun exposure:
        WBGT = 0.7*NWB + 0.3*Temp_globe
            NWB: nature wet-bulb temperature (using Daymet and Humidity to esitiamte GT from Stull 2011) https://journals-ametsoc-org.ezproxy1.lib.asu.edu/view/journals/apme/50/11/jamc-d-11-0143.1.xml
                or: method 2
            GT: Globe Temperature (using MRT to estimate GT Vanos et al., 2021)
            DB: dry bulb temperature. Here assuming DB equals to air temperature equals to Daymet temperature
    '''
    NWB = calculate_NWB_1(trip, RH)
    '''
        NWB = trip.daymet_exp * math.atan(0.151977 * ((RH * 100 + 8.313659) ** (1 / 2))) + math.atan(
            (trip.daymet_exp + RH * 100)) - math.atan(RH * 100 - 1.676331) + 0.00391838 * ((RH * 100) ** (3 / 2)) * math.atan(
            0.023101 * RH * 100) - 4.686035 # Stull 2011 method        
    '''

    # (Ts+273.15)^4+alpha*(Ts+273.15)+belta = 0
    GT = calculate_GT_1(trip, Va)
    # DB: dry bulb temperature. Here assuming DB equals to air temperature
    DB = trip.daymet_exp
    if trip.mrt_exp == trip.daymet_exp: outdoor = False
    if outdoor:
        # outdoor calculation
        trip.wbgt_exp = int(0.7 * NWB + 0.2 * GT + 0.1 * DB)
        # print(f'NWB: {NWB}, GT: {GT}, DB: {DB}, WBGT: {trip.wbgt_exp}')
    else:
        # indoor calculation
        trip.wbgt_exp = int(0.7 * NWB + 0.3 * GT)


@functools.lru_cache(maxsize=5000)  # Limit the cache size to 5 most recent calls
def get_air_temp(tmin: int, tmax: int, time: int, tdawn: int = 6, tpeak: int = 17) -> int:
    if time < tdawn:
        return int((tmax + tmin) / 2 - (tmax - tmin) / 2 * cos(pi * (tdawn - time) / (24 + tdawn - tpeak)))
    elif time < tpeak:
        return int((tmax + tmin) / 2 + (tmax - tmin) / 2 * cos(pi * (tpeak - time) / (tpeak - tdawn)))
    else:
        return int((tmax + tmin) / 2 - (tmax - tmin) / 2 * cos(pi * (24 + tdawn - time) / (24 + tdawn - tpeak)))


def calculate_exposure(trip: Route, network: networkx.Graph, air_dict, mrt_dict) -> None:
    """
    calculate trip heat exposure and update
    :param trip:
    :param network:
    :param air_dict:
    :param mrt_dict:
    :return:
    """
    start_step = trip.abmStart // 3600 + 4
    if (trip.mode in ('walk', 'bike')) and len(trip.route) > 1:

        link_list = list(zip(trip.route[0:-1], trip.route[1:]))
        # steps = dur//15
        link_list = set([tuple(sorted(i)) for i in link_list])

        try:
            _air_dt = [air_dict[_] for _ in link_list]
            _temp_daymet = [get_air_temp(tmin=_t['tmin'], tmax=_t['tmax'], time=start_step) for _t in _air_dt]
            _temp_length = [network.edges[_]['weight'] for _ in link_list]
            update_dataclass(trip, length=int(sum(_temp_length)),
                             daymet_exp=int(
                                 sum([a * b for a, b in zip(_temp_daymet, _temp_length)]) / sum(_temp_length)))
            if (start_step >= 7) & (start_step <= 20):
                try:
                    _temp_temperature = [mrt_dict[_][start_step] for _ in link_list]
                    update_dataclass(trip,
                                     mrt_exp=int(sum([a * b for a, b in zip(_temp_temperature, _temp_length)]) / sum(
                                         _temp_length)))
                    Cal_WBGT(trip, 0.2, 3.2)
                except Exception as e:
                    error_message = e.args[0]  # Get the first argument used to construct the exception
                    error_type = type(e).__name__  # Get the type of the exception
                    print(f"An error of type {error_type} occurred: {error_message}")
                    update_dataclass(trip, mrt_exp=int(trip.daymet_exp)),
                    Cal_WBGT(trip, 0.2, 3.2)
            else:
                update_dataclass(trip, mrt_exp=int(trip.daymet_exp)),
                Cal_WBGT(trip, 0.2, 3.2)
        except Exception as e1:
            error_message = e1.args[0]  # Get the first argument used to construct the exception
            error_type = type(e1).__name__  # Get the type of the exception
            print(f"An error of type {error_type} occurred: {error_message}")
            pass
