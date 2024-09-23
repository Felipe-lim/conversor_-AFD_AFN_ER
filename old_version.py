import sys
import re
from collections import defaultdict, deque

class NFA:
    def __init__(self, states, alphabet, transitions, initial_state, final_states):
        # states: set of states
        # alphabet: set of symbols
        # transitions: dict mapping state to dict of symbol to set of states
        # initial_state: single state
        # final_states: set of states
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions  # dict of dicts
        self.initial_state = initial_state
        self.final_states = set(final_states)

class DFA:
    def __init__(self, states, alphabet, transitions, initial_state, final_states):
        # states: set of frozensets of NFA states
        # alphabet: set of symbols
        # transitions: dict mapping state to dict of symbol to state
        # initial_state: single state (frozenset)
        # final_states: set of states (frozensets)
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
    # Convert infix regex to postfix using shunting-yard algorithm
    def shunting_yard(regex):
        precedence = {'*': 3, '.': 2, '|': 1}
        output = []
        stack = []
        i = 0
        while i < len(regex):
            c = regex[i]
            if c in alphabet:
                output.append(c)
            elif c == '(':
                stack.append(c)
            elif c == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()  # Pop '('
            else:  # Operator
                while (stack and stack[-1] != '(' and
                       precedence.get(c, 0) <= precedence.get(stack[-1], 0)):
                    output.append(stack.pop())
                stack.append(c)
            i += 1
        while stack:
            output.append(stack.pop())
        return output

    # Add concatenation operators '.'
    def add_concat(regex):
        result = ''
        for i in range(len(regex)):
            c1 = regex[i]
            result += c1
            if i + 1 < len(regex):
                c2 = regex[i + 1]
                if (c1 in alphabet or c1 == '*' or c1 == ')') and (c2 in alphabet or c2 == '('):
                    result += '.'
        return result

    # Build NFA from postfix expression
    def build_nfa(postfix):
        stack = []
        for token in postfix:
            if token in alphabet:
                s0 = State()
                s1 = State()
                s0.transitions[token].add(s1)
                stack.append((s0, s1))
            elif token == '*':
                s0 = State()
                s1 = State()
                nfa1 = stack.pop()
                s0.epsilon_transitions.add(nfa1[0])
                s0.epsilon_transitions.add(s1)
                nfa1[1].epsilon_transitions.add(nfa1[0])
                nfa1[1].epsilon_transitions.add(s1)
                stack.append((s0, s1))
            elif token == '.':
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                nfa1[1].epsilon_transitions.add(nfa2[0])
                stack.append((nfa1[0], nfa2[1]))
            elif token == '|':
                s0 = State()
                s1 = State()
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                s0.epsilon_transitions.add(nfa1[0])
                s0.epsilon_transitions.add(nfa2[0])
                nfa1[1].epsilon_transitions.add(s1)
                nfa2[1].epsilon_transitions.add(s1)
                stack.append((s0, s1))
        nfa = stack.pop()
        states = set()
        queue = deque()
        queue.append(nfa[0])
        while queue:
            state = queue.popleft()
            if state not in states:
                states.add(state)
                for symbol in state.transitions:
                    for s in state.transitions[symbol]:
                        queue.append(s)
                for s in state.epsilon_transitions:
                    queue.append(s)
        state_id_map = {state: f'q{idx}' for idx, state in enumerate(states)}
        transitions = defaultdict(lambda: defaultdict(set))
        for state in states:
            state_id = state_id_map[state]
            for symbol in state.transitions:
                for s in state.transitions[symbol]:
                    transitions[state_id][symbol].add(state_id_map[s])
            if state.epsilon_transitions:
                for s in state.epsilon_transitions:
                    transitions[state_id][''].add(state_id_map[s])  # Epsilon transitions
        initial_state = state_id_map[nfa[0]]
        final_states = {state_id_map[nfa[1]]}
        nfa_result = NFA(state_id_map.values(), alphabet, transitions, initial_state, final_states)
        return nfa_result

    regex = add_concat(regex)
    postfix = shunting_yard(regex)
    nfa = build_nfa(postfix)
    return nfa

# Subset construction: NFA to DFA
def nfa_to_dfa(nfa):
    initial_state = frozenset(epsilon_closure(nfa, [nfa.initial_state]))
    dfa_states = set()
    dfa_transitions = {}
    dfa_final_states = set()
    unmarked_states = deque()
    unmarked_states.append(initial_state)
    dfa_states.add(initial_state)
    if nfa.final_states & initial_state:
        dfa_final_states.add(initial_state)
    while unmarked_states:
        current = unmarked_states.popleft()
        dfa_transitions[current] = {}
        for symbol in nfa.alphabet:
            if symbol == '':
                continue  # Skip epsilon
            next_states = move(nfa, current, symbol)
            if not next_states:
                continue
            closure = frozenset(epsilon_closure(nfa, next_states))
            if closure not in dfa_states:
                dfa_states.add(closure)
                unmarked_states.append(closure)
                if nfa.final_states & closure:
                    dfa_final_states.add(closure)
            dfa_transitions[current][symbol] = closure
    dfa = DFA(dfa_states, nfa.alphabet, dfa_transitions, initial_state, dfa_final_states)
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
    # Convert DFA to GNFA
    states = list(dfa.states)
    num_states = len(states)
    state_indices = {state: idx for idx, state in enumerate(states)}
    regex = [[None]*num_states for _ in range(num_states)]
    # Initialize regex table
    for i in range(num_states):
        for j in range(num_states):
            regex[i][j] = set()
    for state in dfa.states:
        idx_from = state_indices[state]
        for symbol in dfa.alphabet:
            if symbol == '':
                continue
            next_state = dfa.transitions.get(state, {}).get(symbol, None)
            if next_state:
                idx_to = state_indices[next_state]
                regex[idx_from][idx_to].add(symbol)
    # Add start and accept states
    start_state = num_states
    accept_state = num_states + 1
    num_states += 2
    regex = [row + [set()] for row in regex]
    regex.append([set() for _ in range(num_states)])
    regex.append([set() for _ in range(num_states)])
    # From new start state to old start state
    regex[start_state][state_indices[dfa.initial_state]].add('')
    # From old final states to new accept state
    for final_state in dfa.final_states:
        idx = state_indices[final_state]
        regex[idx][accept_state].add('')
    # Eliminate states one by one
    for k in range(len(dfa.states)):
        if k == state_indices[dfa.initial_state] or any(k == state_indices[s] for s in dfa.final_states):
            continue
        for i in range(num_states):
            if i == k:
                continue
            for j in range(num_states):
                if j == k:
                    continue
                loop = union(regex[k][k])
                if loop:
                    loop = f'({loop})*'
                else:
                    loop = ''
                r1 = union(regex[i][k])
                r2 = union(regex[k][j])
                if r1 and r2:
                    if loop:
                        term = f'{r1}{loop}{r2}'
                    else:
                        term = f'{r1}{r2}'
                    regex[i][j].add(term)
        # Remove state k
        for i in range(num_states):
            regex[i][k] = set()
            regex[k][i] = set()
    # The regular expression is in regex[start_state][accept_state]
    final_re = union(regex[start_state][accept_state])
    return final_re

def union(regex_set):
    if not regex_set:
        return ''
    elif len(regex_set) == 1:
        return next(iter(regex_set))
    else:
        return '|'.join(sorted(regex_set))

def print_automaton(automaton):
    print('alfabeto:' + ','.join(automaton.alphabet))
    print('estados:' + ','.join(str(s) for s in automaton.states))
    print('inicial:' + str(automaton.initial_state))
    print('finais:' + ','.join(str(s) for s in automaton.final_states))
    print('transicoes')
    for state in automaton.transitions:
        for symbol in automaton.transitions[state]:
            next_states = automaton.transitions[state][symbol]
            for next_state in next_states:
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

