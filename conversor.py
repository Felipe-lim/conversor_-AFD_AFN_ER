import sys
import re
from collections import defaultdict, deque

class NFA:
    def __init__(self, states, alphabet, transitions, initial_state, final_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions  # dict of dicts
        self.initial_state = initial_state
        self.final_states = set(final_states)

class DFA:
    def __init__(self, states, alphabet, transitions, initial_state, final_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions  # dict of dicts
        self.initial_state = initial_state
        self.final_states = set(final_states)

def read_automaton(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    alphabet = []
    states = []
    initial_state = None
    final_states = []
    transitions = defaultdict(lambda: defaultdict(set))
    reading_transitions = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line == 'transicoes':
            reading_transitions = True
            continue
        if not reading_transitions:
            if line.startswith('alfabeto:'):
                alphabet = line[len('alfabeto:'):].split(',')
                alphabet = [sym.strip() for sym in alphabet]
            elif line.startswith('estados:'):
                states = line[len('estados:'):].split(',')
                states = [s.strip() for s in states]
            elif line.startswith('inicial:'):
                initial_state = line[len('inicial:'):].strip()
            elif line.startswith('finais:'):
                final_states = line[len('finais:'):].split(',')
                final_states = [s.strip() for s in final_states]
        else:
            # Read transitions
            parts = line.split(',')
            if len(parts) != 3:
                print(f"Invalid transition line: {line}")
                sys.exit(1)
            from_state = parts[0].strip()
            to_state = parts[1].strip()
            symbol = parts[2].strip()
            transitions[from_state][symbol].add(to_state)

    nfa = NFA(states, alphabet, transitions, initial_state, final_states)
    return nfa

def read_regular_expression(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    alphabet = []
    expression = ''
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('alfabeto:'):
            alphabet = line[len('alfabeto:'):].split(',')
            alphabet = [sym.strip() for sym in alphabet]
        elif line.startswith('expressao:'):
            expression = line[len('expressao:'):].strip()
    return alphabet, expression

# Thompson's construction: RE to NFA
class State:
    def __init__(self):
        self.transitions = defaultdict(set)
        self.epsilon_transitions = set()

def regex_to_nfa(regex, alphabet):
    # (Implementation remains the same)
    # ...
    # (For brevity, I have not included this part again)
    pass

# Subset construction: NFA to DFA
def nfa_to_dfa(nfa):
    # Map frozenset of NFA states to DFA state names
    state_name_mapping = {}
    state_count = 0

    def get_state_name(state_set):
        nonlocal state_count
        if state_set not in state_name_mapping:
            state_name_mapping[state_set] = f'D{state_count}'
            state_count += 1
        return state_name_mapping[state_set]

    initial_state_set = frozenset(epsilon_closure(nfa, [nfa.initial_state]))
    initial_state = get_state_name(initial_state_set)
    dfa_states = set()
    dfa_transitions = {}
    dfa_final_states = set()
    unmarked_states = deque()
    unmarked_states.append(initial_state_set)
    dfa_states.add(initial_state_set)
    if nfa.final_states & initial_state_set:
        dfa_final_states.add(initial_state)
    while unmarked_states:
        current_set = unmarked_states.popleft()
        current_state = get_state_name(current_set)
        dfa_transitions[current_state] = {}
        for symbol in nfa.alphabet:
            if symbol == '':
                continue  # Skip epsilon
            next_states = move(nfa, current_set, symbol)
            if not next_states:
                continue
            closure = frozenset(epsilon_closure(nfa, next_states))
            next_state = get_state_name(closure)
            if closure not in dfa_states:
                dfa_states.add(closure)
                unmarked_states.append(closure)
                if nfa.final_states & closure:
                    dfa_final_states.add(next_state)
            dfa_transitions[current_state][symbol] = next_state
    dfa = DFA(state_name_mapping.values(), nfa.alphabet, dfa_transitions, initial_state, dfa_final_states)
    return dfa

def epsilon_closure(nfa, states):
    stack = list(states)
    closure = set(states)
    while stack:
        state = stack.pop()
        for next_state in nfa.transitions.get(state, {}).get('', []):
            if next_state not in closure:
                closure.add(next_state)
                stack.append(next_state)
    return closure

def move(nfa, states, symbol):
    next_states = set()
    for state in states:
        for next_state in nfa.transitions.get(state, {}).get(symbol, []):
            next_states.add(next_state)
    return next_states

# DFA to Regular Expression (State Elimination)
def dfa_to_re(dfa):
    # (Implementation remains the same)
    # ...
    # (For brevity, I have not included this part again)
    pass

def print_automaton(automaton):
    print('alfabeto:' + ','.join(sorted(automaton.alphabet)))
    print('estados:' + ','.join(automaton.states))
    print('inicial:' + automaton.initial_state)
    print('finais:' + ','.join(automaton.final_states))
    print('transicoes')
    for state in automaton.transitions:
        for symbol in automaton.transitions[state]:
            next_state = automaton.transitions[state][symbol]
            print(f"{state},{next_state},{symbol}")

def main():
    print("Bem-vindo ao conversor AFD/AFN/ER!")
    print("Escolha uma opção:")
    print("1. Converter AFN para AFD")
    print("2. Converter AFD para ER")
    print("3. Converter ER para AFN")
    option = input("Opção (1/2/3): ").strip()
    if option == '1':
        filename = input("Digite o nome do arquivo contendo o AFN: ").strip()
        nfa = read_automaton(filename)
        print("Convertendo AFN para AFD...")
        dfa = nfa_to_dfa(nfa)
        print("Resultado da conversão (AFD):")
        print_automaton(dfa)
    elif option == '2':
        filename = input("Digite o nome do arquivo contendo o AFD: ").strip()
        nfa = read_automaton(filename)
        print("Convertendo AFD para ER...")
        re = dfa_to_re(nfa)
        print("Expressão Regular resultante:")
        print(re)
    elif option == '3':
        filename = input("Digite o nome do arquivo contendo a ER: ").strip()
        alphabet, expression = read_regular_expression(filename)
        print("Convertendo ER para AFN...")
        nfa = regex_to_nfa(expression, alphabet)
        print("Resultado da conversão (AFN):")
        print_automaton(nfa)
    else:
        print("Opção inválida.")
        sys.exit(1)

if __name__ == '__main__':
    main()
