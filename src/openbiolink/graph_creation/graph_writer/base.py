import json
import os
from abc import ABC, abstractmethod
from typing import Mapping, Optional

from openbiolink import globalConfig as globConst, graphProperties
from openbiolink.edge import Edge
from openbiolink.graph_creation import graphCreationConfig as gcConst


class GraphWriter(ABC):
    """A class that can write information to a directory."""

    @abstractmethod
    def write(
        self, *, tp_nodes, tp_edges: Mapping[str, Edge], tp_namespaces, tn_nodes, tn_edges, tn_namespaces,
    ):
        raise NotImplementedError


class OpenBioLinkGraphWriter(GraphWriter):
    """A writer class that abstracts the OpenBioLink RDF and TSV exporters."""

    def __init__(
        self, *, multi_file, print_qscore: bool, file_sep: Optional[str] = None,
    ):
        self.graph_dir_path = os.path.join(globConst.WORKING_DIR, gcConst.GRAPH_FILES_FOLDER_NAME)
        os.makedirs(self.graph_dir_path, exist_ok=True)

        self.multi_file = multi_file
        self.print_qscore = print_qscore
        if file_sep is None:
            file_sep = "\t"
        self.file_sep = file_sep

    def output_graph_props(self):
        graph_prop_dict = {
            key: getattr(graphProperties, key) for key in dir(graphProperties) if not key.startswith("__")
        }

        # Sanitize - not necessary since all types can be dumped to JSON?
        # for k, v in graph_prop_dict.items():
        #    if not isinstance(v, str):
        #        graph_prop_dict[k] = str(v)

        with open(os.path.join(self.graph_dir_path, "graph_props.json"), "w") as file:
            json.dump(graph_prop_dict, file, indent=2)

    def write_node_and_edge_list(self, prefix, nodes_list, edges_list):
        with open(os.path.join(self.graph_dir_path, prefix + "nodes_list.csv"), "w") as out_file:
            out_file.writelines(list("\n".join(nodes_list)))

        with open(os.path.join(self.graph_dir_path, prefix + "edges_list.csv"), "w") as out_file:
            out_file.writelines(list("\n".join(edges_list)))

    @abstractmethod
    def output_graph(
        self,
        nodes: Optional[Mapping] = None,
        edges: Optional[Mapping] = None,
        prefix: Optional[str] = None,
        node_edge_list: bool = True,
    ):
        raise NotImplementedError

    def write(
        self, *, tp_nodes, tp_edges: Mapping[str, Edge], tp_namespaces, tn_nodes, tn_edges, tn_namespaces,
    ):
        # create/output positive edges
        self.output_graph(nodes=tp_nodes, edges=tp_edges)
        # create/output negative edges
        self.output_graph(nodes=tn_nodes, edges=tn_edges, prefix="TN_")

        all_nodes = tp_nodes.copy()
        for key, values in tn_nodes.items():
            if key in all_nodes.keys():
                temp = set(all_nodes[key])
                temp.update(set(values))
                values = temp
            all_nodes[key] = values
        self.output_graph(nodes=all_nodes, edges=None, prefix="ALL_", node_edge_list=False)

        graphProperties.EDGE_TYPES = list(tp_edges.keys())
        graphProperties.NODE_TYPES = list(tp_nodes.keys())
        graphProperties.NODE_NAMESPACES = list(tp_namespaces)
        self.output_graph_props()
