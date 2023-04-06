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
    def __init__(self, n_matrix, edges, verticies, m, p):
        self.N = n_matrix   # Macierz natężeń strumienia pakietów
        self.p = p  # prawdopodobieństwo nieuszkodzenia dowolnej krawędzi
        self.m = m  # średnia wielkość pakietu w bitach
        self.edges = edges
        self.T = 0
        self.copy = nx.Graph()
        for i in range(len(verticies)):
            self.copy.add_node(i)
        self.verticies = verticies
        self.G = sum([sum(row) for row in self.N])  # suma wszystkich elementów macierzy N
        self.generate_c()
        self.generate_a()
        self.T = (1 / self.G) * sum(edge.a / ((edge.c / self.m) - edge.a) for edge in self.edges)

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
    def generate_a(self, split_packets=False):
        self.copy.clear_edges()
        for edge in self.edges:
            edge.a = 0
            x = random.random()
            edge.works = x < self.p
            if edge.works:
                self.copy.add_edge(edge.v1, edge.v2)
        while not nx.is_connected(self.copy):
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
                if not split_packets:   # wysyłanie wszystkich pakietów jedną ścieżką
                    path = self.find_shortest_path(self.verticies[i], self.verticies[j], packets)
                    for k in range(1, len(path)):
                        for edge in self.edges:
                            if good_edge(edge, path[k-1], path[k]):
                                edge.a += packets
                                break
                else:   # wysłanie pakietów rożnymi ścieżkami
                    while packets > 0:
                        path = self.find_shortest_path(self.verticies[i], self.verticies[j], 1)
                        edges = []
                        for k in range(1, len(path)):
                            for edge in self.edges:
                                if good_edge(edge, path[k-1], path[k]):
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
    def generate_c(self):
        for edge in self.edges:
            edge.c = 10000

    # Metoda zwiększająca funkcje przepustowości o stałą wartość
    def increase_c(self, const):
        for i in range(len(self.edges)):
            if self.edges[i].c == 0:
                self.edges[i].c += const

    # Metoda testująca niezawodność sieci. Rzeczywista niezawodnosc , niezawodnosc , % rozspojnien
    def test_reliability(self, T_max, reps):
        passed = 0
        for i in range(reps):
            try:
                self.generate_a()
                if self.T < T_max:
                    passed += 1
            except nx.exception.NetworkXNoPath:
                pass
        return round(passed / reps * 100, 2)

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
        self.edges.append(Edge(a, b, c=20000))


if __name__ == "__main__":
    par = argparse.ArgumentParser()
    par.add_argument("-z", "--zad", choices=["1", "2", "3", "4"], help="Numer podpunktu z zadania.")
    par.add_argument("-t", "--t_max", help="Maksymalne opoznienie")
    par.add_argument("-p", "--probability", help="Prawdopodobienstwo nieuszkodzenia połączenia")
    par.add_argument("-m", "--avg_size", help="Sredni rozmiar pakietu")

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

    _verticies = [i for i in range(20)]     # 20 wierzcholkow i 31 krawedzi
    _edges = [Edge(0, 1), Edge(1, 2), Edge(2, 3), Edge(3, 4), Edge(4, 5), Edge(5, 6), Edge(6, 7), Edge(7, 8),
              Edge(8, 9), Edge(9, 10), Edge(10, 11), Edge(11, 12), Edge(12, 13), Edge(13, 14), Edge(14, 15),
              Edge(15, 16), Edge(16, 17), Edge(17, 18), Edge(18, 19), Edge(19, 0),
              Edge(19, 9, 20000), Edge(0, 10, 20000)]
    network = Network(n_matrix=generate_matrix(20), edges=_edges, verticies=_verticies, m=M, p=pr)

    if args.zad == "1":
        reli = network.test_reliability(t_max, 1000)
        print(f"Niezawodność sieci - {reli}%")
    elif args.zad == "2":
        try:
            var = int(input("Podaj stałą o którą zwiększane badą wartości N: "))
            times = int(input("Podaj max ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa Niezawodność {reli}%")
            for i in range(times):
                network.increase_N(var)
                reli = network.test_reliability(t_max, 2000)
                print(f"N zwiększone o {(i+1)*var} - Niezawodność {reli}%")
                if reli < 5:
                    break

        except ValueError:
            print("Błędne parametry")
            exit(-1)
    elif args.zad == "3":
        try:
            var = int(input("Podaj stałą o którą zwiększana bedzie przepustowosc: "))
            times = int(input("Podaj ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa Niezawodność {reli}%")
            for i in range(times):
                network.increase_c(var)
                reli = network.test_reliability(t_max, 2000)
                print(f"Przepustowosc zwiększona o {(i+1)*var} bitów - Niezawodność {reli}%")
                if reli > 99:
                    break

        except ValueError:
            print("Błędne parametry")
            exit(-1)
    elif args.zad == "4":
        try:
            times = int(input("Podaj ilość powtórzeń: "))
            reli = network.test_reliability(t_max, 2000)
            print(f"Początkowa Niezawodność {reli}%")
            for i in range(times):
                network.add_random_edge()
                print(f"- {network.test_reliability(t_max, 2000)}%")

        except ValueError:
            print("Błędne parametry")
            exit(-1)

