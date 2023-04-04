import random
import networkx as nx


class Edge:
    def __init__(self, v1, v2, c=0):
        self.v1 = v1
        self.v2 = v2
        self.a = 0  # rzeczywisty przepływ ( liczba pakietów )
        self.c = c  # przepustowość ( max liczba bitów )
        self.works = True


# Funkcja sprawdzająca czy podana krawędź jest szukaną
def good_edge(edge, v1, v2):
    if (edge.v1 == v1 and edge.v2 == v2) or (edge.v1 == v2 and edge.v2 == v1):
        return True
    return False


class Network:
    def __init__(self, n_matrix, edges, verticies, m=10, p=1.0):
        self.N = n_matrix   # Macierz natężeń strumienia pakietów
        self.p = p  # prawdopodobieństwo nieuszkodzenia dowolnej krawędzi
        self.m = m  # średnia wielkość pakietu w bitach
        self.edges = edges
        self.verticies = verticies
        self.G = sum([sum(row) for row in self.N])  # suma wszystkich elementów macierzy N
        self.generate_a(first_iter=True)

    # Metoda zwracająca naszybszą ścieżkę z v(i) do v(j) po której może przejść podana liczba pakietów
    def find_shortest_path(self, v_i, v_j, packets, first_iter):
        nxGraph = nx.Graph()
        for vertex in self.verticies:
            nxGraph.add_node(vertex)
        # Do grafu dodawane są krawędzie które po przesłaniu dodatkowej liczby pakietów nie przekroczą przepustowości.
        for edge in [ed for ed in self.edges if (ed.works and ed.c > ed.a + packets) or first_iter]:
            nxGraph.add_edge(edge.v1, edge.v2)
        return nx.dijkstra_path(nxGraph, v_i, v_j)

    # Generowanie funkcji przepływu zgodnie z obecną macierzą N oraz funkcją przepustowości.
    def generate_a(self, first_iter=False, split_packets=False):
        for edge in self.edges:
            if not first_iter:
                edge.works = random.random() <= self.p
        for i in range(len(self.N)):
            for j in range(len(self.N[i])):
                packets = self.N[i][j]  # ilość pakietow do przesłania z v(i) do v(j)

                if not split_packets:   # wysyłanie wszystkich pakietów jedną ścieżką
                    path = self.find_shortest_path(self.verticies[i], self.verticies[j], packets, first_iter)
                    for k in range(1, len(path)):
                        for edge in self.edges:
                            if good_edge(edge, path[k-1], path[k]):
                                edge.a += packets
                                break
                else:   # wysłanie pakietów rożnymi ścieżkami
                    while packets != 0:
                        path = self.find_shortest_path(self.verticies[i], self.verticies[j], 1, first_iter)
                        edges = []
                        for k in range(1, len(path)):
                            for edge in self.edges:
                                if good_edge(edge, path[k-1], path[k]):
                                    edges.append(self.edges.index(edge))
                                    break
                        # maksymalna liczba pakietów możliwa do wysłania daną najkrótszą ścieżką
                        sent = min([self.edges[idx].c / self.m - self.edges[idx].a for idx in edges]) - 1
                        if sent > packets:
                            sent = packets
                        for idx in edges:
                            self.edges[idx].a += sent
                        packets -= sent


if __name__ == "__main__":
    exit(0)
