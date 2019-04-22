import time

import datetime
import pytz
import calendar
import itertools
import pandas as pd
import numpy as np

import sys
import os

import networkx as nx
import plotly.offline as py

import itertools
import xbos_services_getter as xsg

from Optimizers import OptimizerParent


# TODO Demand charges right now assume constant demand charge throughout interval. should be easy to extend
# TODO but need to keep in mind that we need to then store the cost of demand charge and not the consumption
# TODO in the graph, since we actually only want to minimize cost and not consumption.

# TODO if there is no feasible solution in which we can stay within a safety region –– revert to standard control and force it to go within saftey region.

class Node:
    """
    # this is a Node of the graph for the shortest path
    """

    def __init__(self, temperatures, timestep):
        self.temperatures = temperatures
        self.timestep = timestep

    def __hash__(self):
        return hash((' '.join(str(e) for e in self.temperatures), self.timestep))

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.temperatures == other.temperatures \
               and self.timestep == other.timestep

    def __repr__(self):
        return "{0}-{1}".format(self.timestep, self.temperatures)


class MPC(OptimizerParent.OptimizerParent):
    """MPC Optimizer.
    No Demand Charges and Two Stage actions implemented."""

    def __init__(self, building, zones, start, end, window, lambda_val,
                 non_controllable_data=None, debug=False):
        """
        initialize instance variables

        :param building: (str) building name
        :param zones: [str] zone names
        :param start: (datetime timezone aware)
        :param end: (datetime timezone aware)
        :param window: (str) the interval in which to split the data.
        :param lambda_val: (float) lambda value for opjective function

        """
        super().__init__(building, zones, start, end, window, non_controllable_data)

        self.lambda_val = lambda_val
        self.debug = debug

        self.g = nx.DiGraph()  # [TODO:Changed to MultiDiGraph... FIX print]

    def safety_check(self, node):
        for iter_zone in self.zones:
            curr_temperature = node.temperatures[iter_zone]
            curr_safety = self.do_not_exceed[iter_zone].iloc[node.timestep]
            if not (curr_safety["t_low"] <= curr_temperature <= curr_safety["t_high"]):
                return False
        return True

    def timestep_to_datetime(self, timestep):
        return self.start + timestep * datetime.timedelta(seconds=xsg.get_window_in_sec(self.window))

    # the shortest path algorithm
    def shortest_path(self, root):
        """
        Creates the graph using DFS and calculates the shortest path

        :param root: node being examined right now and needs to be added to graph.

        :return: root Node if root added else return None.

        """

        if root is None:
            return None

        if root in self.g:
            return root

        # stop if node is past predictive horizon
        if self.timestep_to_datetime(root.timestep) >= self.end:
            self.g.add_node(root, objective_cost=0, best_action=None, best_successor=None)  # no cost as leaf node
            return root

        # check if valid node
        if not self.safety_check(root):
            return None

        self.g.add_node(root, objective_cost=np.inf, best_action=None, best_successor=None)

        # creating children, adding corresponding edge and updating root's objective cost
        for action in itertools.product([xsg.NO_ACTION, xsg.HEATING_ACTION, xsg.COOLING_ACTION],
                                        repeat=len(self.zones)):

            # TODO Compute temperatures properly
            temperatures = {}
            zone_actions = {}
            for i in range(len(self.zones)):
                zone_actions[self.zones[i]] = action[i]
                temperatures[self.zones[i]] = root.temperatures[self.zones[i]] + \
                                              1 * (action[i] == 1) - 1 * (action[i] == 2)

            # Create child node and call the shortest_path recursively on it
            child_node = Node(
                temperatures=temperatures,
                timestep=root.timestep + 1
            )

            child_node = self.shortest_path(child_node)
            if child_node is None:
                continue

            # get discomfort across edge
            discomfort = {}
            for iter_zone in self.zones:
                curr_comfortband = self.comfortband[iter_zone].iloc[root.timestep]
                curr_occupancy = self.occupancy[iter_zone].iloc[root.timestep]
                average_edge_temperature = (root.temperatures[iter_zone] + child_node.temperatures[iter_zone]) / 2.

                discomfort[iter_zone] = xsg.get_discomfort(
                    self.discomfort_stub, self.building, average_edge_temperature,
                    curr_comfortband["t_low"], curr_comfortband["t_high"],
                    curr_occupancy)

            # Get consumption across edge
            price = 1  # self.prices.iloc[root.timestep] TODO also add right unit conversion, and duration
            consumption_cost = {self.zones[i]: price * self.hvac_consumption[self.zones[i]][action[i]]
                                for i in range(len(self.zones))}

            # add edge
            self.g.add_edge(root, child_node, action=zone_actions, discomfort=discomfort,
                            consumption_cost=consumption_cost)

            # update root node to contain the best child.
            total_edge_cost = ((1 - self.lambda_val) * (sum(consumption_cost.values()))) + (
                    self.lambda_val * (sum(discomfort.values())))

            objective_cost = self.g.node[child_node]["objective_cost"] + total_edge_cost

            if objective_cost < self.g.node[root]["objective_cost"]:
                self.g.node[root]["objective_cost"] = objective_cost
                self.g.node[root]["best_action"] = zone_actions
                self.g.node[root]["best_successor"] = child_node

        return root

    def reconstruct_path(self, root):
        """
        Util function that reconstructs the best action path
        Parameters
        ----------
        graph : networkx graph

        Returns
        -------
        List
        """
        graph = self.g

        if root not in self.g:
            raise Exception("Root does not exist in MPC graph.")

        path = [root]

        while graph.node[root]['best_successor'] is not None:
            root = graph.node[root]['best_successor']
            path.append(root)

        return path

#     def g_plot(self, zone):
#         try:
#             os.remove('mpc_graph_' + zone + '.html')
#         except OSError:
#             pass

#         fig = plotly_figure(self.advise_unit.g, path=self.path)
#         py.plot(fig, filename='mpc_graph_' + zone + '.html', auto_open=False)

    def advise(self, starting_temperatures):
        """Call this function to get best action.

        :param starting_temperatures: dict {zone: float temperature}
        :return: action, err
        """
        root = Node(starting_temperatures, 0)
        root = self.shortest_path(root)
        if root is None:
            return None, "Could not find feasible action."

        return self.g.node[root]["best_action"], None
