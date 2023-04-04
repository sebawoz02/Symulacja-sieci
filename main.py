import random
import networkx as nx
import argparse


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


# Funkcja generująca macierz natężeń n x n ( od 1 do 8 pakietów )
def generate_matrix(n):
    matrix = []
    for i in range(n):
        matrix.append([random.randint(1, 8) if i != j else 0 for j in range(n)])
    return matrix


class Network:
    def __init__(self, n_matrix, edges, verticies, m, p):
        self.N = n_matrix   # Macierz natężeń strumienia pakietów
        self.p = p  # prawdopodobieństwo nieuszkodzenia dowolnej krawędzi
        self.m = m  # średnia wielkość pakietu w bitach
        self.edges = edges
        self.T = 0
        self.verticies = verticies
        self.G = sum([sum(row) for row in self.N])  # suma wszystkich elementów macierzy N
        self.generate_a(first_iter=True)
        self.generate_c()

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
            edge.a = 0
            if not first_iter:
                x = random.random()
                edge.works = x < self.p
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
                    while packets > 0:
                        path = self.find_shortest_path(self.verticies[i], self.verticies[j], 1, first_iter)
                        edges = []
                        for k in range(1, len(path)):
                            for edge in self.edges:
                                if good_edge(edge, path[k-1], path[k]):
                                    edges.append(self.edges.index(edge))
                                    break
                        # maksymalna liczba pakietów możliwa do wysłania daną najkrótszą ścieżką
                        sent = min([self.edges[idx].c / self.m - self.edges[idx].a for idx in edges])
                        if sent > packets:
                            sent = packets
                        else:
                            sent = int(sent)
                        for idx in edges:
                            self.edges[idx].a += sent
                        packets -= sent
        self.T = (1 / self.G) * sum(edge.a / ((edge.c / self.m) - edge.a) for edge in self.edges)

    # Metoda generująca przepustwość dla krawędzi.
    def generate_c(self):
        m = max([edge.a for edge in self.edges])
        for edge in self.edges:
            edge.c = random.randint(2, 5) * m * self.m

    # Metoda testująca niezawodność sieci.
    def test_reliability(self, T_max, reps):
        itr = 0
        for i in range(reps):
            try:
                self.generate_a(split_packets=True)
                if self.T < T_max:
                    itr += 1
            except nx.exception.NetworkXNoPath:
                pass
        return itr / reps * 100


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-z", "--zad", choices=["1", "2", "3", "4"], help="Numer podpunktu z zadania.")
    par.add_argument("-t", "--t_max")
    par.add_argument("-p", "--probability")
    par.add_argument("-m", "--avg_size", help="Sredni rozmiar pakietu")

    args = par.parse_args()
    try:
        pr = float(args.probability)
    except TypeError:
        pr = 0.97
    try:
        t_max = float(args.t_max)
    except TypeError:
        t_max = 0.99
    try:
        M = int(args.avg_size)
    except TypeError:
        M = 10

    _verticies = [i for i in range(20)]
    _edges = [Edge(0, 15), Edge(0, 1), Edge(0, 5), Edge(1, 6), Edge(1, 2), Edge(2, 3), Edge(2, 7), Edge(3, 4),
              Edge(3, 8), Edge(4, 19), Edge(4, 9), Edge(5, 10), Edge(5, 6), Edge(6, 11), Edge(6, 7), Edge(7, 8),
              Edge(7, 12), Edge(8, 9), Edge(8, 13), Edge(9, 14), Edge(10, 15), Edge(10, 11), Edge(11, 12), Edge(11, 16),
              Edge(12, 13), Edge(12, 17), Edge(13, 14), Edge(13, 18), Edge(14, 19), Edge(15, 19), Edge(15, 16),
              Edge(16, 17), Edge(17, 18), Edge(18, 19)]
    network = Network(n_matrix=generate_matrix(20), edges=_edges, verticies=_verticies, m=M, p=pr)

    if args.zad == "1":
        rel = network.test_reliability(t_max, 1000)
        print(f"Niezawodność sieci - {rel}%")
