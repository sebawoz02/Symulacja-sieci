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


# Funkcja generująca macierz natężeń n x n ( od 1 do 5 pakietów )
def generate_matrix(n):
    matrix = []
    for i in range(n):
        matrix.append([random.randint(1, 5) if i != j else 0 for j in range(n)])
    return matrix


class Network:
    def __init__(self, n_matrix, edges, verticies, m, p, val):
        self.N = n_matrix  # Macierz natężeń strumienia pakietów
        self.p = p  # prawdopodobieństwo nieuszkodzenia dowolnej krawędzi
        self.m = m  # średnia wielkość pakietu w bitach
        self.edges = edges
        self.T = 0
        self.copy = nx.Graph()
        for i in range(len(verticies)):
            self.copy.add_node(i)
        self.verticies = verticies
        self.G = sum([sum(row) for row in self.N])  # suma wszystkich elementów macierzy N
        self.generate_c(val)
        self.generate_a(first_generate=True)
        self.T = (1 / self.G) * sum(edge.a / ((edge.c / self.m) - edge.a) for edge in self.edges)
        self.failures = 0

    # Metoda zwracająca naszybszą ścieżkę z v(i) do v(j) po której może przejść podana liczba pakietów
    def find_shortest_path(self, v_i, v_j, packets):
        nxGraph = nx.Graph()
        for vertex in self.verticies:
            nxGraph.add_node(vertex)
        # Do grafu dodawane są krawędzie które po przesłaniu dodatkowej liczby pakietów nie przekroczą przepustowości.
        for edge in [ed for ed in self.edges if (ed.works and (ed.c / self.m) > (ed.a + packets))]:
            nxGraph.add_edge(edge.v1, edge.v2)
        return nx.dijkstra_path(nxGraph, v_i, v_j)

    # Generowanie funkcji przepływu zgodnie z obecną macierzą N oraz funkcją przepustowości.
    def generate_a(self, split_packets=False, first_generate=False):
        self.copy.clear_edges()
        for edge in self.edges:
            edge.a = 0
            x = random.random()
            if not first_generate:
                edge.works = x < self.p
            if edge.works:
                self.copy.add_edge(edge.v1, edge.v2)
        while not nx.is_connected(self.copy):
            self.failures += 1
            self.copy.clear_edges()
            for edge in self.edges:
                edge.a = 0
                x = random.random()
                edge.works = x < self.p
                if edge.works:
                    self.copy.add_edge(edge.v1, edge.v2)
        for i in range(len(self.N)):
            for j in range(len(self.N[i])):
                packets = self.N[i][j]  # ilość pakietow do przesłania z v(i) do v(j)
                if not split_packets:  # wysyłanie wszystkich pakietów jedną ścieżką
                    path = self.find_shortest_path(self.verticies[i], self.verticies[j], packets)
                    for k in range(1, len(path)):
                        for edge in self.edges:
                            if good_edge(edge, path[k - 1], path[k]):
                                edge.a += packets
                                break
                else:  # wysłanie pakietów rożnymi ścieżkami
                    while packets > 0:
                        path = self.find_shortest_path(self.verticies[i], self.verticies[j], 1)
                        edges = []
                        for k in range(1, len(path)):
                            for edge in self.edges:
                                if good_edge(edge, path[k - 1], path[k]):
                                    edges.append(self.edges.index(edge))
                                    break
                        # maksymalna liczba pakietów możliwa do wysłania daną najkrótszą ścieżką
                        sent = int(min([self.edges[idx].c / self.m - self.edges[idx].a for idx in edges]))
                        if sent > packets:
                            sent = packets
                        else:
                            sent = int(sent)
                        for idx in edges:
                            self.edges[idx].a += sent
                        packets -= sent
        self.T = (1 / self.G) * sum(edge.a / ((edge.c / self.m) - edge.a) for edge in self.edges)

    # Metoda generująca przepustwość dla krawędzi. W tym przypadku dwukrotnosc aktualnego przeplywu
    def generate_c(self, val):
        for edge in self.edges:
            edge.c = val

    # Metoda zwiększająca funkcje przepustowości o stałą wartość
    def increase_c(self, const):
        for i in range(len(self.edges)):
            self.edges[i].c += const

    # Metoda testująca niezawodność sieci. Zwraca niezawodnosc oraz procent rozspojnien
    def test_reliability(self, T_max, reps):
        self.failures = 0
        passed = 0
        iters = 0
        for i in range(reps):
            try:
                self.generate_a()
                iters += 1
                if self.T < T_max:
                    passed += 1
            except nx.exception.NetworkXNoPath:
                pass
        if iters > 0:
            ret = round((iters - passed) / reps * 100, 2)
        else:
            ret = 0.0
        return round(passed / reps * 100, 2), round(self.failures / (self.failures + reps) * 100, 2), ret

    # Metoda zwiększająca wartosci w macierzy N o podaną wartość całkowitą
    def increase_N(self, val):
        for i in range(len(self.N)):
            for j in range(len(self.N)):
                if i != j:
                    self.N[i][j] += val

    # Metoda dodająca losową nową krawędź
    def add_random_edge(self):
        a = random.randint(0, 19)
        b = random.randint(0, 19)
        exists = False
        for edge in self.edges:
            if good_edge(edge, a, b):
                exists = True
                break
        while exists:
            a = random.randint(0, 19)
            b = random.randint(0, 19)
            exists = False
            for edge in self.edges:
                if good_edge(edge, a, b):
                    exists = True
                    break
        self.edges.append(Edge(a, b, c=4000))


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-z", "--zad", choices=["1", "2", "3", "4"], help="Numer podpunktu z zadania.")
    par.add_argument("-t", "--t_max", help="Maksymalne opoznienie")
    par.add_argument("-p", "--probability", help="Prawdopodobienstwo nieuszkodzenia połączenia")
    par.add_argument("-m", "--avg_size", help="Sredni rozmiar pakietu")
    par.add_argument("-g", "--graph", choices=["1", "2"], help="Wybierz graf do testów")

    args = par.parse_args()
    try:
        pr = float(args.probability)
    except TypeError:
        pr = 0.97
    try:
        t_max = float(args.t_max)
    except TypeError:
        t_max = 1e-2
    try:
        M = int(args.avg_size)
    except TypeError:
        M = 10
    try:
        if int(args.graph) == 1:
            c_val = 6000
        else:
            c_val = 5000
    except TypeError:
        print("Nie wybrano grafu")
        exit(-1)

    _verticies = [i for i in range(20)]  # 20 wierzcholkow i 31 krawedzi
    _edges = [Edge(0, 1), Edge(1, 2), Edge(2, 3), Edge(3, 4), Edge(4, 5), Edge(5, 6), Edge(6, 7), Edge(7, 8),
              Edge(8, 9), Edge(9, 10), Edge(10, 11), Edge(11, 12), Edge(12, 13), Edge(13, 14), Edge(14, 15),
              Edge(15, 16), Edge(16, 17), Edge(17, 18), Edge(18, 19), Edge(19, 0),
              Edge(19, 9, 12000), Edge(0, 10, 12000)]
    _edges2 = [Edge(0, 1), Edge(1, 2), Edge(0, 5, 3000), Edge(2, 3), Edge(2, 7, 3000), Edge(3, 4),
               Edge(4, 9, 3000), Edge(5, 10, 3000), Edge(5, 6), Edge(6, 7), Edge(7, 8), Edge(8, 9), Edge(9, 14, 3000),
               Edge(10, 11), Edge(10, 15, 3000), Edge(11, 12), Edge(12, 13), Edge(12, 17, 3000), Edge(13, 14),
               Edge(14, 19, 3000), Edge(15, 16), Edge(16, 17), Edge(17, 18), Edge(18, 19)]
    if int(args.graph) == 1:
        network = Network(n_matrix=generate_matrix(20), edges=_edges, verticies=_verticies, m=M, p=pr, val=c_val)
    else:
        network = Network(n_matrix=generate_matrix(20), edges=_edges2, verticies=_verticies, m=M, p=pr, val=c_val)
    if args.zad == "1":
        reli = network.test_reliability(t_max, 1000)
        print(f"Niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
              f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
              f", Czestotliwość rozspójnień - {reli[1]}%")
    elif args.zad == "2":
        try:
            var = int(input("Podaj stałą o którą zwiększane badą wartości N: "))
            times = int(input("Podaj max ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
                  f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                  f", Czestotliwość rozspójnień - {reli[1]}%")
            for i in range(times):
                network.increase_N(var)
                reli = network.test_reliability(t_max, 2000)
                print(f"N zwiększone o {(i + 1) * var} - Niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
                      f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                      f", Czestotliwość rozspójnień - {reli[1]}%")

        except ValueError:
            print("Błędne parametry")
            exit(-1)
    elif args.zad == "3":
        try:
            var = int(input("Podaj stałą o którą zwiększana bedzie przepustowosc: "))
            times = int(input("Podaj ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
                  f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                  f", Czestotliwość rozspójnień - {reli[1]}%")
            for i in range(times):
                network.increase_c(var)
                reli = network.test_reliability(t_max, 2000)
                print(f"Przepustowosc zwiększona o {(i + 1) * var} bitów - Niezawodność {reli[0]}% "
                      f"({reli[2]}% przekroczone opóźnienie,"
                      f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                      f", Czestotliwość rozspójnień - {reli[1]}%")

        except ValueError:
            print("Błędne parametry")
            exit(-1)
    elif args.zad == "4":
        try:
            times = int(input("Podaj ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
                  f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                  f", Czestotliwość rozspójnień - {reli[1]}%")
            for i in range(times):
                network.add_random_edge()
                reli = network.test_reliability(t_max, 2000)
                print(f"- Niezawodność {reli[0]}% ({reli[2]}% przekroczone opóźnienie,"
                      f" {round(100 - reli[0] - reli[2], 2)}% przekroczona przepustowosc)"
                      f", Czestotliwość rozspójnień - {reli[1]}%")

        except ValueError:
            print("Błędne parametry")
            exit(-1)

