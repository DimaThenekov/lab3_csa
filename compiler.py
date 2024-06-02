import sys

COMPILE_SETUP = {
    "MIN_ABS_VALUE_FOR_STORE_NUMBER_IN_CONSTANTS": 127,
    "STACK_SIZE": 512,  # *4 bytes
}


def tokenize(programm):
    in_string = False
    _string = ""
    _string_q = ""
    in_varible = False
    _varible = ""
    types = ["int32", "int16", "int8", "str", "void"]
    moves = ["do", "while", "for", "if"]
    math = ["&&", "||", ",", ">>", "<<", "+", "-", "%", "*", "!=", "==", "<", ">", "=", "[", "]", "(", ")", "{", "}"]
    sep = [" ", "\t", "\r"]
    instruction_sep = [";", "\n"]
    string_q = ["'", '"', "`"]
    i = 0
    tokens = []
    while i < len(programm):
        end = False
        if in_string:  # END OF STRING
            if programm.startswith(_string_q, i):
                tokens.append({"v": _string, "t": "STRING", "pos": i - len(_string) - len(_string_q)})  # TODO TEST -1
                in_string = False
                i += len(_string_q)
                continue
            _string += programm[i]
            i += 1
            continue

        if programm.startswith("/*", i):
            pos = programm.find("*/", i)
            if pos == -1:
                print("comment at " + str(i) + " not closed")
                exit(1)
            i = pos + 2
            continue

        if programm.startswith("//", i):
            pos = programm.find("\n", i)
            if pos == -1:
                break
            i = pos
            continue

        for s in string_q:  # START OF STRING
            if programm.startswith(s, i):
                end = True
                if in_varible:
                    tokens.append({"v": _varible, "t": "VARIBLE", "pos": i - len(_varible)})  # TODO TEST -1
                    in_varible = False
                in_string = True
                _string = ""
                _string_q = s
                i += len(s)
                break
        if end:
            continue

        for s in sep:  # NO VARIBLE: , \t
            if programm.startswith(s, i):
                end = True
                if in_varible:
                    tokens.append({"v": _varible, "t": "VARIBLE", "pos": i - len(_varible)})  # TODO TEST -1
                    in_varible = False
                i += len(s)
                break
        if end:
            continue

        for s in instruction_sep:  # ;, \n
            if programm.startswith(s, i):
                end = True
                if in_varible:
                    tokens.append({"v": _varible, "t": "VARIBLE", "pos": i - len(_varible)})
                    in_varible = False
                tokens.append({"t": "SEPARATOR", "pos": i})
                i += len(s)
                break
        if end:
            continue

        for s in math:  # OPERATORS
            if programm.startswith(s, i):
                end = True
                if in_varible:
                    tokens.append({"v": _varible, "t": "VARIBLE", "pos": i - len(_varible)})
                    in_varible = False
                tokens.append({"v": s, "t": "MATH", "pos": i})
                i += len(s)
                break
        if end:
            continue

        if in_varible:
            _varible += programm[i]
            i += 1
            continue

        for s in moves:
            if programm.startswith(s, i):
                end = True
                tokens.append({"v": s, "t": "BRANCHING", "pos": i})
                i += len(s)
                break
        if end:
            continue

        for s in types:
            if programm.startswith(s, i):
                end = True
                tokens.append({"v": s, "t": "TYPE", "pos": i})
                i += len(s)
                break
        if end:
            continue

        in_varible = True
        _varible = programm[i]
        i += 1
    if in_string:
        print("string at " + str(i - len(_string)) + " not closed")
        exit(1)
    if in_varible:
        tokens.append({"v": _varible, "t": "VARIBLE", "pos": i - len(_varible)})

    def check_and_transforn_number(x):
        if x["t"] != "VARIBLE":
            return x
        import re

        if re.match(r"(0|[1-9]\d*)", x["v"]):
            x["v"] = int(x["v"])
            x["t"] = "NUMBER"
            return x
        else:
            return x

    tokens = list(map(check_and_transforn_number, tokens))
    return tokens


ast_errors = []


class ASTNode:
    def __init__(self, value, type, pos, children=None):
        self.value = value
        self.type = type
        self.pos = pos
        self.children = [] if children is None else children


def build_ast(tokens):
    # do REMOVE_TOKEN(); while (f != True)
    def skip_sep(tokens):
        if not tokens:
            ast_errors.append("Unexpected EOF")
            return False
        while (len(tokens) > 0) and (tokens[0] is not None) and tokens[0]["t"] == "SEPARATOR":
            tokens.pop(0)
        if not tokens:
            ast_errors.append("Unexpected EOF")
            return False
        return True

    # do REMOVE_TOKEN(); while (f != True)
    def check(tokens, f):
        if not tokens:
            ast_errors.append("Unexpected EOF")
            return True
        if not f(tokens[0]):
            ast_errors.append(
                "Unexpected token "
                + ('"' + tokens[0]["v"] + '" ' if "v" in tokens[0] else "")
                + "at "
                + str(tokens[0]["pos"])
            )
            return True
        return False

    # <branching> ::= do {<instructions>} while (<formula>) |
    #                 while (<formula>) {<instructions>} |
    #                 for (<instr>;<formula>;<instr>) {<instructions>} |
    #                 if (<formula>) {<instructions>}
    def parse_branching(tokens):
        if not tokens:
            return None
        b_type = tokens.pop(0)  # ["do", "while", "for", "if"]
        node = ASTNode(b_type["v"], "BRANCHING", b_type["pos"])
        if not skip_sep(tokens):
            return node

        if b_type["v"] == "do":
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "{"):
                return node
            tokens.pop(0)
            node.children = parse_instructions(tokens)
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "}"):
                return node
            tokens.pop(0)
            if not skip_sep(tokens):
                return node
            if check(tokens, lambda x: x["t"] == "BRANCHING" and x["v"] == "while"):
                return node
            tokens.pop(0)
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "("):
                return node
            tokens.pop(0)
            node.children.append(parse_formula(tokens))
            if node.children[-1] is None:
                return node
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == ")"):
                return node
            tokens.pop(0)
            return node
        if b_type["v"] == "for":
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "("):
                return node
            tokens.pop(0)
            node.children.append(parse_instr(tokens))
            if node.children[-1] is None:
                return node
            if check(tokens, lambda x: x["t"] == "SEPARATOR"):
                return node
            tokens.pop(0)
            node.children.append(parse_formula(tokens))
            if node.children[-1] is None:
                return node
            if check(tokens, lambda x: x["t"] == "SEPARATOR"):
                return node
            tokens.pop(0)
            node.children.append(parse_instr(tokens))
            if node.children[-1] is None:
                return node
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == ")"):
                return node
            tokens.pop(0)
            if not skip_sep(tokens):
                return node
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "{"):
                return node
            tokens.pop(0)
            if not skip_sep(tokens):
                return node
            node.children.append(ASTNode("BODY", "INSTRUCTIONS", tokens[0]["pos"], parse_instructions(tokens)))
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "}"):
                return node
            tokens.pop(0)
            return node
        if b_type["v"] == "if" or b_type["v"] == "while":
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "("):
                return node
            tokens.pop(0)
            node.children.append(parse_formula(tokens))
            if node.children[-1] is None:
                return node
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == ")"):
                return node
            tokens.pop(0)
            if not skip_sep(tokens):
                return node
            if tokens[0]["t"] == "MATH" and tokens[0]["v"] == "{":  # have body
                tokens.pop(0)
                node.children.append(ASTNode("BODY", "INSTRUCTIONS", tokens[0]["pos"], parse_instructions(tokens)))
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "}"):
                    return node
                tokens.pop(0)
            else:
                node.children.append(ASTNode("BODY", "INSTRUCTIONS", tokens[0]["pos"], [parse_instr(tokens)]))
            return node
        return None

    # <typed_args> ::= <type> <name> | <typed_args>, <type> <name>
    def parse_args(tokens):
        if not tokens:
            return []
        list = []
        while tokens:
            if tokens[0]["t"] == "MATH" and tokens[0]["v"] == ")":
                break
            if check(tokens, lambda x: x["t"] == "TYPE"):
                # print('1')
                return None
            _type = tokens.pop(0)
            if check(tokens, lambda x: x["t"] == "VARIBLE"):
                # print('2')
                return None
            _name = tokens.pop(0)
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] in (",", ")")):
                # print('3')
                return None
            list.append([_type["v"], _name["v"], _type["pos"]])
            if tokens[0]["v"] == ")":
                break
            tokens.pop(0)
        return list

    # [
    #     "&&", "||", ","
    #     ">>", "<<", "+", "-", "%", "*",
    #     "!=", "==", "<", ">",
    #     "[", "]", "(", ")"
    # ]
    #
    # <args> ::= <formula_0> | <args>,<formula_0)>
    # <formula_n> ::=        <name>(<args>) | <name> | <name>[<formula_0>] | <number> | (<formula_0>)
    #                  n==0: <formula_1> || <formula_0> |
    #                  n<=1: <formula_2> && <formula_1> |
    #                  n<=2: <formula_3> == <formula_3> | <formula_3> != <formula_3> |
    #                          <formula_3> < <formula_3> | <formula_3> > <formula_3> |
    #                  n<=3: <formula_4> << <formula_4> | <formula_4> >> <formula_4> |
    #                  n<=4: <formula_5> * <formula_4> | <formula_5> % <formula_4> |
    #                  n<=5: <formula_6> + <formula_5> |  <formula_6> - <formula_5>
    def parse_formula(tokens):
        if not tokens:
            return None

        node = ASTNode("FORMULA", "FORMULA", tokens[0]["pos"])
        input_stack = []
        tmp = 0
        while tokens:
            child = tokens[0]
            if child is None:
                break
            if child["t"] == "MATH" and child["v"] == "(":
                tmp += 1
            if child["t"] == "MATH" and child["v"] == "[":
                tmp += 1
            if child["t"] == "MATH" and child["v"] == ")":
                tmp -= 1
                if tmp < 0:
                    break
            if child["t"] == "MATH" and child["v"] == "]":
                tmp -= 1
                if tmp < 0:
                    break
            if child["t"] == "MATH" and child["v"] == ",":
                if tmp <= 0:
                    break
            if child["t"] == "SEPARATOR":
                if tmp <= 0:
                    break
                continue
            if child["t"] == "MATH" and child["v"] in ("{", "}"):
                if tmp <= 0:
                    break
                else:
                    ast_errors.append(
                        "Unexpected token "
                        + ('"' + tokens[0]["v"] + '" ' if "v" in tokens[0] else "")
                        + "at "
                        + str(tokens[0]["pos"])
                    )
                    break
            input_stack.append(child)
            tokens.pop(0)

        input_stack = list(reversed(input_stack))
        output_tokens = []
        tokens_stack = []
        remove_stack = []  # trash
        if not input_stack:
            ast_errors.append("2Unexpected token at " + str(node.pos))
            return node
        t = input_stack[-1]

        def move(stack1, stack2):
            if stack1:
                stack2.append(stack1.pop())
                return False
            ast_errors.append("Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"]))
            return True

        def cmp_op(op1, op2):
            # operators = ['!', '**', '*', '/', '+', '-', '<=', '>=', '<>', '=', '<', '>', '&&', '||'];
            ar = ["%", "*", "+", "-", ">>", "<<", "!=", "==", "<", ">", "&&", "||"]
            return ar.index(op1) <= ar.index(op2)

        while input_stack:
            t = input_stack[-1]
            if t["t"] == "VARIBLE":
                if len(input_stack) > 1 and input_stack[-2]["t"] == "MATH" and input_stack[-2]["v"] == "(":
                    if move(input_stack, tokens_stack):
                        break
                    if move(input_stack, tokens_stack):
                        break
                    continue
                if len(input_stack) > 1 and input_stack[-2]["t"] == "MATH" and input_stack[-2]["v"] == "[":
                    if move(input_stack, tokens_stack):
                        break
                    if move(input_stack, tokens_stack):
                        break
                    continue
                if move(input_stack, output_tokens):
                    break
            elif t["t"] == "NUMBER":
                move(input_stack, output_tokens)
            elif t["t"] == "STRING":
                move(input_stack, output_tokens)
            elif t["t"] == "MATH" and t["v"] in ("&&", "||", ">>", "<<", "+", "-", "%", "*", "!=", "==", "<", ">"):
                while (
                    len(tokens_stack)
                    and tokens_stack[-1]["t"] == "MATH"
                    and tokens_stack[-1]["v"] in ("&&", "||", ">>", "<<", ",", "+", "-", "%", "*", "!=", "==", "<", ">")
                    and cmp_op(tokens_stack[-1]["v"], t["v"])
                ):
                    if move(tokens_stack, output_tokens):
                        break
                if move(input_stack, tokens_stack):
                    break
            elif t["t"] == "MATH" and t["v"] == "(":
                if move(input_stack, tokens_stack):
                    break
                # if input_stack and input_stack[-1]["t"] == "VARIBLE":
                #    if move(input_stack, tokens_stack):
                #        break
            elif t["t"] == "MATH" and t["v"] == ")":
                while (
                    tokens_stack
                    and tokens_stack[-1]["t"] == "MATH"
                    and tokens_stack[-1]["v"] in ("&&", "||", ">>", "<<", ",", "+", "-", "%", "*", "!=", "==", "<", ">")
                ):
                    if move(tokens_stack, output_tokens):
                        break
                if len(tokens_stack) == 0 or not (tokens_stack[-1]["t"] == "MATH" and tokens_stack[-1]["v"] == "("):
                    ast_errors.append(
                        "Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"])
                    )
                    break
                if move(tokens_stack, remove_stack):
                    break
                if len(tokens_stack) and tokens_stack[-1]["t"] == "VARIBLE":
                    tokens_stack[-1]["t"] = "CALC_FUNCTION"
                    if move(tokens_stack, output_tokens):
                        break
                if move(input_stack, remove_stack):
                    break
            elif t["t"] == "MATH" and t["v"] == "[":
                ast_errors.append(
                    "Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"])
                )
                break
            elif t["t"] == "MATH" and t["v"] == "]":
                while (
                    len(tokens_stack)
                    and tokens_stack[-1]["t"] == "MATH"
                    and tokens_stack[-1]["v"] in ("&&", "||", ">>", "<<", ",", "+", "-", "%", "*", "!=", "==", "<", ">")
                ):
                    move(tokens_stack, output_tokens)
                if len(tokens_stack) == 0 or not (tokens_stack[-1]["t"] == "MATH" and tokens_stack[-1]["v"] == "["):
                    ast_errors.append(
                        "Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"])
                    )
                    break
                if move(tokens_stack, remove_stack):
                    break
                if move(tokens_stack, output_tokens):
                    break
                if move(input_stack, remove_stack):
                    break
                output_tokens[-1]["t"] = "CALC_ARRAY"
            elif t["t"] == "MATH" and t["v"] == ",":
                while (
                    tokens_stack
                    and tokens_stack[-1]["t"] == "MATH"
                    and tokens_stack[-1]["v"] in ("&&", "||", ">>", "<<", ",", "+", "-", "%", "*", "!=", "==", "<", ">")
                ):
                    if move(tokens_stack, output_tokens):
                        break
                if len(tokens_stack) < 2 or not (
                    tokens_stack[-1]["t"] == "MATH"
                    and tokens_stack[-1]["v"] == "("
                    and tokens_stack[-2]["t"] == "VARIBLE"
                ):
                    ast_errors.append(
                        "Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"])
                    )
                    break
                tokens_stack[-2]["v"] += "-"
                if move(input_stack, remove_stack):
                    break
            else:
                ast_errors.append(
                    "Unexpected token " + ('"' + t["v"] + '" ' if "v" in t else "") + "at " + str(t["pos"])
                )
                break

        if input_stack:
            return node
        while (
            tokens_stack
            and tokens_stack[-1]["t"] == "MATH"
            and tokens_stack[-1]["v"] in ("&&", "||", ">>", "<<", ",", "+", "-", "%", "*", "!=", "==", "<", ">")
        ):
            move(tokens_stack, output_tokens)
        node.children = list(map(lambda x: ASTNode(x["v"], x["t"], x["pos"]), output_tokens))
        if tokens_stack:
            ast_errors.append(
                "Unexpected token "
                + ('"' + tokens_stack[-1]["v"] + '" ' if "v" in tokens_stack[-1] else "")
                + "at "
                + str(tokens_stack[-1]["pos"])
            )
        return node

    # <instr> ::= <branching> |
    #             <type> <name>(<typed_args>) {<instructions>} | <type> <name>=<formula> | <type> <name>[<formula>] |
    #             <name>=<formula> | <name>[<formula>]=<formula> | <name>(<args>)
    def parse_instr(tokens):
        if not tokens:
            return None
        current_token = tokens[0]

        if current_token["t"] == "BRANCHING":  # <instr> ::= <branching>
            return parse_branching(tokens)

        elif current_token["t"] == "TYPE":
            var_type = tokens.pop(0)["v"]
            if check(tokens, lambda x: x["t"] == "VARIBLE"):
                return None
            var_name = tokens.pop(0)["v"]
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] in ("[", "=", "(")):
                return None
            if tokens[0]["v"] == "=":  # <instr> ::= <type> <name>=<formula>
                tokens.pop(0)
                ch = parse_formula(tokens)
                if ch is None:
                    return None
                return ASTNode(
                    {"type": var_type, "name": var_name}, "DECLARAT_VARIBLE", current_token["pos"], ch.children
                )
            elif tokens[0]["v"] == "[":  # <instr> ::= <type> <name>[<formula>]
                tokens.pop(0)
                ch = parse_formula(tokens)
                if ch is None:
                    return None
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "]"):
                    return None
                tokens.pop(0)
                return ASTNode(
                    {"type": "A" + var_type, "name": var_name}, "DECLARAT_ARRAY", current_token["pos"], ch.children
                )
            elif tokens[0]["v"] == "(":  # <instr> ::= <type> <name>(<arg>) {<instructions>}
                tokens.pop(0)
                ch = parse_args(tokens)
                if ch is None:
                    return None
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == ")"):
                    return None
                tokens.pop(0)
                if not skip_sep(tokens):
                    return node
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "{"):
                    return None
                tokens.pop(0)
                body = parse_instructions(tokens)
                if not skip_sep(tokens):
                    return node
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "}"):
                    return None
                tokens.pop(0)
                if var_type != "void":
                    ch.insert(0, ["int32", "return", current_token["pos"]])
                return ASTNode(
                    {"type": var_type, "name": var_name, "args": ch}, "DECLARAT_FUNCTION", current_token["pos"], body
                )
            return parse_formula(tokens)

        elif current_token["t"] == "VARIBLE":
            var_name = tokens.pop(0)["v"]
            if check(tokens, lambda x: x["t"] == "MATH" and x["v"] in ("=", "(", "[")):
                return None
            if tokens[0]["v"] == "=":  # <instr> ::= <name>=<formula>
                tokens.pop(0)
                ch = parse_formula(tokens)
                if ch is None:
                    return None
                return ASTNode(var_name, "ASSIGN", current_token["pos"], ch.children)
            elif tokens[0]["v"] == "(":  # <instr> ::= <name>(<args>)
                tokens.pop(0)
                formuls = []
                while True:
                    if tokens and tokens[0]["t"] == "MATH" and tokens[0]["v"] == ")":
                        break
                    ch = parse_formula(tokens)
                    if ch is None:
                        return None
                    if check(tokens, lambda x: x["t"] == "MATH" and x["v"] in (",", ")")):
                        return None
                    formuls.append(ch)
                    if tokens[0]["v"] == ")":
                        break
                tokens.pop(0)
                return ASTNode(var_name, "EVAL_PROCEDURE", current_token["pos"], formuls)
            elif tokens[0]["v"] == "[":  # <name>[<formula>]=<formula>
                tokens.pop(0)
                ch = parse_formula(tokens)
                if ch is None:
                    return None
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "]"):
                    return None
                tokens.pop(0)
                if check(tokens, lambda x: x["t"] == "MATH" and x["v"] == "="):
                    return None
                tokens.pop(0)
                ch2 = parse_formula(tokens)
                if ch2 is None:
                    return None
                return ASTNode(var_name, "ASSIGN_ARRAY", current_token["pos"], [ch, ch2])
        ast_errors.append('Unexpected token "' + current_token["v"] + '" at ' + str(current_token["pos"]))
        return None

    # parse inner functions
    # <instructions> ::= <пусто> | <instr> | <instr><instructions>
    def parse_instructions(tokens):
        nodes = []
        while tokens:
            current_token = tokens[0]
            child = None
            if current_token["t"] == "MATH" and current_token["v"] == "}":
                break
            elif current_token["t"] == "SEPARATOR":
                tokens.pop(0)
                continue
            else:
                child = parse_instr(tokens)
                if child is None:
                    while (len(tokens) > 0) and (tokens[0] is not None) and (tokens[0]["t"] != "SEPARATOR"):
                        tokens.pop(0)
                    continue
            if child is None:
                break
            nodes.append(child)
        return nodes

    remaining_tokens = tokens.copy()
    # <programm> ::= <instructions>
    return ASTNode("main", "INSTRUCTIONS", 0, parse_instructions(remaining_tokens))


# Printing the AST for visualization
def print_ast(node, indent=0):
    if node is None:
        return
    print("    " * indent + str(node.value) + " (" + node.type + ", " + str(node.pos) + ")")
    for child in node.children:
        print_ast(child, indent + 1)


# print_ast(ast)

# CPU registers:
# EAX (16bit: AX, 8bit: AL) - 32-bit ACCUMULATOR. General purpose register
# SP - 32-bit STACK POINTER
# IP - 32-bit INSTRUCTION POINTER
# CPU 4 flags: OF - overflow, C - carry, Z - zero, S - sign

# MEM(32 bit address) = 32bit value by address
#            000      001        010         011          100         101          110         111
# F(ARG) ::= ARG || MEM(ARG) || A+ARG || MEM(A+ARG) ||  IP+ARG || MEM(IP+ARG) ||  SP+ARG || MEM(SP+ARG)

# A ::= AL || AX || EAX || RESERVED_FOR_x64

# 0000xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx NOP            NOP
# 0001xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx HALT           HALT

# 0010RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            A := F(ARG)            Z S
# MOV AL, -10
# MOV AL, [A-2]
# MOV AL, [IP+2]
# MOV AL, SP
# 0011RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            MEM(F(ARG)) := A
# MOV [10], AH
# MOV [SP+10], AL
# MOV [[IP-1]], EAX

# OP ::= ADC || ADD || SBC || SUB || OR || XOR || AND || MUL || SHR || SHL || CMP
# 0100RRxx.OPERxFFF.AAAAAAAA.AAAAAAAA ALU OP ARG                             OF C Z S
# ALU ADC AL [IP+2]
# ALU ADD EAX -10

# UOP ::= NOT || NEG || RCL || RCR || ZEXT8 || ZEXT16 || EXT8 || EXT16
# 0101xxxx.OPERxxxx.xxxxxxxx.xxxxxxxx ALU UOP                                OF C Z S
# ALU NOT
# ALU RCR

# 0110xxxx.00000001.xxxxxxxx.xxxxxxxx OUT         WRITE(AL);
# 0110xxxx.00000010.xxxxxxxx.xxxxxxxx IN          AL := READ()
# 0110xxxx.00000011.xxxxxxxx.xxxxxxxx MALLOC32    EAX := MALLOC(EAX)
# 0110xxxx.00000100.xxxxxxxx.xxxxxxxx MALLOC16    EAX := MALLOC((1+EAX)>>1)<<1
# 0110xxxx.00000101.xxxxxxxx.xxxxxxxx MALLOC8     EAX := MALLOC((3+EAX)>>2)<<2
# 0110xxxx.00000110.xxxxxxxx.xxxxxxxx FREE        FREE(EAX);

# COND = {
#   : 0000  # always
#   E: 0001  # = (Z = 1)
#   NE: 0010  # != (Z = 0)
#   G: 0011  # > ((S xor OF) or Z = 0)
#   L: 0100  # < (S xor OF = 1)
#   GE: 0101  # >= (S xor OF = 0)
#   LE: 0110  # <= ((S xor OF) or Z = 1)
# }
# 1000xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA CALL        MEM(++SP) = IP; IP = F(ARG)
# 1001xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA RET         IP = MEM(SP--)
# 1010xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA JUMP        IP = F(ARG)
# 1011xxxx.xxxxxFFF.AAAAAAAA.AAAAAAAA PUSH        MEM(++SP) = F(ARG)
# 1100xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx POP         F(ARG) = MEM(SP--)            Z S
# 1101RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA SWAP        B=A; A=MEM(F(ARG)); MEM(F(ARG))=B            Z S
# SWAP EAX, SP

# 0000: JUMP [IP+1001]     # START
# 0001: WORD 4321          # GLOBAL CONSTANTS
# 0...: WORD ...
# 1000: WORD 0
# 1001: MOV AL, [4]         # START
# 1002: INT OUT
# 1003: PUSH 2
# 1004: PUSH 3
# 1005: CALL [IP+3]
# 1006: INT OUT
# 1007: HALT
# 1008: MOV EAX, [SP-1]    # FUNCTION A+B
# 1009: ALU ADD [SP-2]
# 1010: MOV [SP-2], EAX
# 1011: RET
compile_errors = []


class ASMdata:
    def __init__(self, name, datatype, type, pos, is_global=False, value={}):
        self.name = name
        self.datatype = datatype
        self.type = type  # f || v || s
        self.pos = pos
        self.is_global = is_global
        self.value = value
        self.fullname = type + ":" + name + ":" + str(pos)


def get_size_type(type, for_array=False):
    if for_array == True:
        if type == "str":
            return 1
        if type[0] == "A":
            type = type[1:]
    if type == "void":
        return -1
    if type == "int8":
        return 1
    if type == "int16":
        return 2
    return 4


def get_register_by_size(size):
    if size == 1:
        return "AL"
    if size == 2:
        return "AX"
    if size == 4:
        return "EAX"
    add_error("")


def compileAST(AST):
    global_const_vars = []
    global_functions = []
    global_variables = []
    output_asm = []

    def add_error(node, text=""):
        compile_errors.append(
            'Unexpected token "'
            + str(node.value)
            + '" at '
            + str(node.pos)
            + (" with message: " + text if text != "" else "")
        )
        return None

    def compile_formila(tokens, stack):
        # print('---')
        asm = []
        for i in tokens:
            # print(i.value, i.type, i.pos)
            if i.type == "NUMBER":
                asm.append("PUSH " + str(i.value))  # TODO MIN_ABS_VALUE_FOR_STORE_NUMBER_IN_CONSTANTS
            elif i.type == "VARIBLE":
                find = False
                for e in reversed(stack):
                    if e.split(":")[0] != "f" and e.split(":")[1] == i.value:
                        asm.append("MOV %R" + e + "%, [%" + e + "%]")
                        asm.append("PUSH EAX")
                        find = True
                        break
                if not find:
                    add_error(i, "variable not declared")
                    return []
            elif i.type == "MATH":
                if i.value == "&&":
                    asm.append("POP")
                    asm.append("AND [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "||":
                    asm.append("POP")
                    asm.append("OR [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == ">>":
                    asm.append("POP")
                    asm.append("SWAP [SP]")
                    asm.append("SHR [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "<<":
                    asm.append("POP")
                    asm.append("SWAP [SP]")
                    asm.append("SHL [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "+":
                    asm.append("POP")
                    asm.append("ADD [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "-":
                    asm.append("POP")
                    asm.append("SWAP [SP]")
                    asm.append("SUB [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "%":
                    asm.append("POP")
                    asm.append("SWAP [SP]")
                    asm.append("MOD [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value == "*":
                    asm.append("POP")
                    asm.append("MUL [SP]")
                    asm.append("MOV [SP], EAX")
                elif i.value in ("==", "!=", "<", ">"):
                    asm.append("POP")
                    asm.append("CMP [SP]")
                    asm.append("JMP " + ["E", "NE", "G", "L"][["==", "!=", "<", ">"].index(i.value)] + " IP+2")
                    asm.append("MOV EAX, 0")
                    asm.append("JMP IP+1")
                    asm.append("MOV EAX, -1")
                    asm.append("MOV [SP], EAX")
                else:
                    add_error("")
            elif i.type == "CALC_ARRAY":
                find = False
                fe = ""
                for e in reversed(stack):
                    if e.split(":")[0] != "f" and e.split(":")[1] == i.value:
                        asm.append("MOV EAX, [%" + e + "%]")
                        fe = e
                        find = True
                        break
                if not find:
                    add_error(i, "array not declared")
                asm.append("ADD [SP]")
                asm.append("MOV %AR" + fe + "%, [EAX]")
                asm.append("MOV [SP], EAX")
            elif i.type == "CALC_FUNCTION":
                if i.value == "IN":
                    asm.append("INT IN")
                    asm.append("PUSH EAX")
                else:
                    find = False
                    for e in reversed(stack):
                        if e.split(":")[0] == "f" and e.split(":")[1] == i.value.split("-")[0]:
                            asm.append("CALL %" + e + "%")
                            find = True
                            break
                    if not find:
                        for i in range(max(i.value.count("-") - 1, 0)):
                            asm.append("POP")
                        add_error(i, "function not declared")
                    else:
                        pass
            elif i.type == "STRING":  # TODO link if exists
                asm.append("PUSH %g:" + str(len(global_variables)) + ":" + str(i.pos) + "%")
                global_variables.append({"type": "string", "value": i.value, "pos": i.pos})
            else:
                print(i.type)
                add_error("")
        return asm

    def compile_branch(node, root, scope):
        asm = []
        for i in node.children:
            if i.type in ("DECLARAT_VARIBLE", "DECLARAT_ARRAY"):
                asm_f = compile_formila(i.children, scope)
                for e in asm_f:
                    asm.append(e)
                asm.append("POP")
                size = get_size_type(i.value["type"], i.type == "DECLARAT_ARRAY")
                if i.type == "DECLARAT_ARRAY":
                    asm.append("INT MALLOC" + str(8 * size))
                asm.append(
                    "MOV [%v:"
                    + i.value["name"]
                    + ":"
                    + str(i.pos)
                    + "%], "
                    + (get_register_by_size(size) if i.type != "DECLARAT_ARRAY" else "EAX")
                    + " # :="
                )
                if "v:" + i.value["name"] + ":" + str(i.pos) not in scope:
                    scope.append("v:" + i.value["name"] + ":" + str(i.pos))
            elif i.type == "ASSIGN_ARRAY":
                asm_index = compile_formila(i.children[0].children, scope)  # index
                for e in asm_index:
                    asm.append(e)
                asm_value = compile_formila(i.children[1].children, scope)  # value
                for e in asm_value:
                    asm.append(e)
                find = False
                fe = ""
                for e in reversed(scope):
                    if e.split(":")[0] != "f" and e.split(":")[1] == i.value:
                        asm.append("MOV EAX, [%" + e + "%]")
                        fe = e
                        find = True
                        break
                if not find:
                    add_error(i, "array not declared")
                asm.append("ADD [SP-1]")
                asm.append("SWAP [SP]")
                asm.append("MOV [[SP]], %AR" + fe + "%")
                asm.append("POP")
                asm.append("POP")
            elif i.type == "ASSIGN":
                asm_value = compile_formila(i.children, scope)  # value
                for e in asm_value:
                    asm.append(e)
                find = False
                asm.append("POP")
                for e in reversed(scope):
                    if e.split(":")[0] != "f" and e.split(":")[1] == i.value:
                        asm.append("MOV [%" + e + "%], %R" + e + "%")
                        find = True
                        break
                if not find:
                    add_error(i, "variable not declared")
            elif i.type == "EVAL_PROCEDURE":
                for j in i.children:
                    asm_arg = compile_formila(j.children, scope)  # arg
                    for e in asm_arg:
                        asm.append(e)
                find = False
                if i.value == "OUT":
                    find = True
                    asm.append("POP")
                    asm.append("INT OUT")
                    asm.append("PUSH 0")  # ???
                elif i.value == "HALT":
                    find = True
                    asm.append("HALT")
                else:
                    for e in reversed(scope):
                        if e.split(":")[0] == "f" and e.split(":")[1] == i.value:
                            asm.append("CALL %" + e + "% # eval procedure")
                            find = True
                            break
                if not find:
                    add_error(i, "functions not declared")
                for j in i.children:
                    asm.append("POP")
            elif i.type == "BRANCHING":
                if i.value == "do":  # do{body}while(condition)
                    condition = i.children.pop()
                    asm_do_b = compile_branch(i, root, scope.copy())  # body
                    for e in asm_do_b:
                        asm.append(e)
                    asm_do_condition = compile_formila(condition.children, scope)  # condition
                    for e in asm_do_condition:
                        asm.append(e)
                    asm.append("POP")
                    asm.append("CMP 0")
                    asm.append("JMP NE IP-" + str(len(asm_do_condition) + len(asm_do_b) + 3) + " # do condition")
                if i.value == "for":  # for(init; condition; step){body}
                    init = i.children.pop(0)
                    condition = i.children.pop(0)
                    # step
                    body = i.children.pop()

                    for_scope = scope.copy()  # init
                    asm_f = compile_formila(init.children, for_scope)
                    for e in asm_f:
                        asm.append(e)
                    asm.append("POP")
                    size = get_size_type(init.value["type"])
                    asm.append(
                        "MOV [%v:"
                        + init.value["name"]
                        + ":"
                        + str(init.pos)
                        + "%], "
                        + get_register_by_size(size)
                        + " # for init"
                    )
                    for_scope.append("v:" + init.value["name"] + ":" + str(init.pos))

                    asm_for_b = compile_branch(body, root, for_scope.copy())  # body
                    for e in asm_for_b:
                        asm.append(e)
                    asm_for_step = compile_branch(i, root, for_scope.copy())  # step
                    for e in asm_for_step:
                        asm.append(e)

                    asm_condition = compile_formila(condition.children, for_scope)  # condition
                    for e in asm_condition:
                        asm.append(e)
                    asm.append("POP")
                    asm.append("CMP 0")
                    asm.append("JMP NE IP-" + str(len(asm_for_b) + len(asm_for_step) + 3) + " # for condition")
                if i.value == "while":  # while(condition){body}
                    asm_while_condition = compile_formila(i.children[0].children, scope)
                    asm_while_b = compile_branch(i.children[1], root, scope.copy())

                    for e in asm_while_condition:  # condition
                        asm.append(e)
                    asm.append("POP")
                    asm.append("CMP 0")
                    asm.append("JMP E IP+" + str(len(asm_while_b) + 1) + " # while condition")

                    for e in asm_while_b:  # body
                        asm.append(e)

                    asm.append("JMP IP-" + str(len(asm_while_b) + len(asm_while_condition) + 4) + " # while jamp")
                if i.value == "if":  # while(condition){body}
                    asm_if_condition = compile_formila(i.children[0].children, scope)  # condition
                    for e in asm_if_condition:
                        asm.append(e)

                    asm_if_b = compile_branch(i.children[1], root, scope.copy())  # body

                    asm.append("POP")
                    asm.append("CMP 0")
                    asm.append("JMP E IP+" + str(len(asm_if_b)) + " # if condition")

                    for e in asm_if_b:
                        asm.append(e)
            else:
                print("ERROR " + i.type)
        return asm

    def compile_global_function(node):  # get array ASMdata
        global_offset = 0
        asm_data = [
            ASMdata(
                "",
                "void",
                "f",
                node.pos,
                True,
                {"node": node, "offset": 0, "global_offset": 0, "args": [], "constants": global_variables},
            )
        ]

        def calc_vars_and_funcs(node, root, i=0):
            in_global = i < 2 and root.value["node"].type == "INSTRUCTIONS"
            if node.type in ("DECLARAT_VARIBLE", "DECLARAT_ARRAY"):
                size = get_size_type(node.value["type"])
                if size < 0:
                    return add_error(node, "void cannot be a variable type")
                # if in_global:
                #    nonlocal global_offset
                #    while global_offset%size!=0: global_offset+=1 # alignment
                #    asm_data.append(ASMdata(node.value["name"], node.value["type"], 'v', node.pos, in_global, {"offset": global_offset}))
                #    global_offset+=size
                # else:
                offset_key = "global_offset" if in_global else "offset"
                while root.value[offset_key] % size != 0:
                    root.value[offset_key] += 1  # alignment
                asm_data.append(
                    ASMdata(
                        node.value["name"],
                        node.value["type"],
                        "v",
                        node.pos,
                        in_global,
                        {"offset": root.value[offset_key]},
                    )
                )
                root.value[offset_key] += size
                return node
            elif node.type == "DECLARAT_FUNCTION" and i > 0:
                asm_data.append(
                    ASMdata(
                        node.value["name"],
                        node.value["type"],
                        "f",
                        node.pos,
                        in_global,
                        {"node": node, "offset": 0, "args": node.value["args"]},
                    )
                )
                return None
            else:
                ch_list = []
                for a in node.children:
                    ch = calc_vars_and_funcs(a, root, i + 1)
                    if ch is not None:
                        ch_list.append(ch)
                node.children = ch_list
                return node

        while True:
            data = None
            for i in asm_data:
                if "node" in i.value:
                    data = i
                    break
            if data is None:
                break
            calc_vars_and_funcs(data.value["node"], data)
            # print('---')
            # print(data.name)
            # print_ast(data.value["node"])
            data.value["cut_node"] = data.value["node"]
            del data.value["node"]
        global_stack = []
        for i in asm_data:
            # print(i.name, i.datatype, i.type, i.is_global, i.value)
            if i.is_global and i.name != "":
                global_stack.append(i.fullname)
        # print(global_stack)
        for i in asm_data:
            if i.type == "f":
                scope = global_stack.copy()
                if i.name != "":
                    scope.append(i.fullname)
                for arg in i.value["args"]:
                    scope.append("v:" + arg[1] + ":" + str(arg[2]))
                i.value["asm"] = compile_branch(i.value["cut_node"], i, scope)
                # print(i.name)
                # print(' - '+'\n - '.join(i.value["asm"]))
        return asm_data

    return compile_global_function(AST)


# Example:
#   PUSH 9
#   POP
#   INT MALLOC32
#   MOV [%v:board:0%], EAX
#   PUSH %g:0:24%
#   POP
#   MOV [%v:s:16%], EAX

# ╔═════════════════╗
# ║    JMP START    ║
# ╚═════════════════╝
# ╔═════════════════╗
# ║      STACK      ║ # STACK_ADR = 1
# ╚═════════════════╝
# ╔═════════════════╗
# ║ GLOBAL VARIBLE  ║ # GLOBAL_VARIBLE_ADR = STACK_ADR + COMPILE_SETUP.STACK_SIZE
# ╚═════════════════╝
# ╔═════════════════╗
# ║ STRINGs         ║ # CONSTANTS_ADR = GLOBAL_VARIBLE_ADR + SIZE(GLOBAL VARIBLE)
# ║        /        ║
# ║        big NUMs ║
# ╚═════════════════╝
# ╔═════════════════╗
# ║ START:          ║
# ║   main programm ║
# ║                 ║
# ║ FUNCTION 1:     ║
# ║   PUSH 0        ║ # local variable
# ║   ...           ║ # n-arg by addres SP-SIZE(local variable)-SIZE(args)-1+n
# ║                 ║
# ║ FUNCTION 2:     ║
# ║   ...           ║
# ║                 ║
# ║ ...             ║
# ║                 ║
# ║ FUNCTION N:     ║
# ║   ...           ║
# ╚═════════════════╝


# def get_size_type(type)
# def get_register_by_size(size)


def linkASM(asm_datas):
    def string_to_bytes(string):
        return [byte for byte in string.encode("utf-8")]

    def string_to_int32_array(string):
        list = string_to_bytes(string)
        list.append(0)
        while len(list) % 4 != 0:
            list.append(0)
        int32_list = []
        for i in range(0, len(list), 4):
            int32_list.append(list[i + 3] + (list[i + 2] << 8) + (list[i + 1] << 16) + (list[i] << 24))
        return int32_list

    def find_value_between_percents(input_string):
        start_percent_index = input_string.find("%")
        if start_percent_index == -1:
            return None
        end_percent_index = input_string.find("%", start_percent_index + 1)
        if end_percent_index == -1:
            return None
        return input_string[start_percent_index + 1 : end_percent_index]

    def replace_value_between_percents(input_string, new_value):
        start_percent_index = input_string.find("%")
        if start_percent_index == -1:
            return input_string
        end_percent_index = input_string.find("%", start_percent_index + 1)
        if end_percent_index == -1:
            return input_string
        return input_string[:start_percent_index] + new_value + input_string[end_percent_index + 1 :]

    link_address = []
    global_const = []

    def linkFunction(asm_data):
        for i in link_address:
            if (i["name"] == asm_data.name) and (i["pos"] == asm_data.pos):
                return
        link_address.append({"name": asm_data.name, "pos": asm_data.pos, "adr": str(len(ASM))})
        start = len(ASM)
        for i in asm_data.value["asm"]:
            ASM.append(i)
        end = len(ASM)
        stack_size = 0
        for i in range(start, end):
            cmd = ASM[i].split("#")[0].strip().split(" ")
            for key in range(len(cmd)):
                percents_text = find_value_between_percents(cmd[key])
                if percents_text is not None:
                    # print(percents_text)
                    percents_text = percents_text.split(":")

                    def find_varible(name, pos, for_array=False):
                        for i in asm_datas:
                            if i.type == "v" and i.name == name and i.pos == pos:
                                if i.is_global:
                                    return (
                                        get_register_by_size(get_size_type(i.datatype, for_array)),
                                        str(
                                            (ASM_info["GLOBAL_VARIBLE_ADR"] + i.value["offset"])
                                            // get_size_type(i.datatype)
                                        ),
                                    )
                                else:
                                    return (
                                        get_register_by_size(get_size_type(i.datatype, for_array)),
                                        "SP-"
                                        + str((stack_size * 4 - i.value["offset"] - 4) // get_size_type(i.datatype)),
                                    )
                        for i in range(len(asm_data.value["args"])):
                            if asm_data.value["args"][i][1] == name and asm_data.value["args"][i][2] == pos:
                                return (
                                    get_register_by_size(get_size_type(asm_data.value["args"][i][0], for_array)),
                                    "SP-" + str(stack_size + len(asm_data.value["args"]) - i),
                                )

                    if percents_text[0] == "g":
                        find = False
                        for j in global_const:
                            if (j["type"] == "string") and (j["pos"] == int(percents_text[2])):
                                cmd[key] = replace_value_between_percents(cmd[key], j["addres"])
                                find = True
                        if not find:
                            print("compile error 1161")
                            exit(1)
                    elif percents_text[0] == "f":
                        find = None
                        for j in asm_datas:
                            if j.type == "f" and j.name == percents_text[1] and j.pos == int(percents_text[2]):
                                find = j
                        if find is None:
                            print("compile error 1169")
                            exit(1)
                        linkFunction(find)
                        for j in link_address:
                            if j["name"] == percents_text[1] and j["pos"] == int(percents_text[2]):
                                cmd[key] = replace_value_between_percents(cmd[key], j["adr"])
                    elif percents_text[0] == "Rv":
                        cmd[key] = replace_value_between_percents(
                            cmd[key], find_varible(percents_text[1], int(percents_text[2]))[0]
                        )
                    elif percents_text[0] == "ARv":
                        cmd[key] = replace_value_between_percents(
                            cmd[key], find_varible(percents_text[1], int(percents_text[2]), True)[0]
                        )
                    elif percents_text[0] == "v":
                        cmd[key] = replace_value_between_percents(
                            cmd[key], find_varible(percents_text[1], int(percents_text[2]))[1]
                        )
                    else:
                        print("compile error 1150")
                        exit(1)

            ASM[i] = " ".join(cmd) + (" #" + ASM[i].split("#")[1] if ASM[i].find("#") > 0 else "")
            if cmd[0] == "PUSH":
                stack_size += 1
            if cmd[0] == "POP":
                stack_size -= 1
        if stack_size != 0:
            print("compile error 1132")
            exit(1)

    ASM_info = {"STACK_ADR": 1, "GLOBAL_VARIBLE_ADR": 1, "CONSTANTS_ADR": 1, "START_ADR": 1}
    ASM = [""]
    ASM_info["STACK_ADR"] = len(ASM) * 4
    for i in range(COMPILE_SETUP["STACK_SIZE"]):
        ASM.append("WORD32 0")
    ASM_info["GLOBAL_VARIBLE_ADR"] = len(ASM) * 4
    while asm_datas[0].value["global_offset"] % 4 != 0:
        asm_datas[0].value["global_offset"] += 1
    for i in range(asm_datas[0].value["global_offset"] // 4):
        ASM.append("WORD32 -1")
    # for i in asm_datas:
    #    if i.type=='v':
    #        if i.is_global:
    #            global_scope.append({"name": i.name, "type": i.datatype, "pos": i.pos, "addres": str((ASM_info["GLOBAL_VARIBLE_ADR"] + i.value["offset"])//get_size_type(i.datatype))})
    #        else
    #            global_scope.append({"name": i.name, "type": i.datatype, "pos": i.pos, "addres": 'SP-'str(i.value["offset"])})

    CONSTANTS_ADR = len(ASM) * 4
    for i in asm_datas[0].value["constants"]:
        if i["type"] == "string":
            global_const.append({"name": i["value"], "type": "string", "pos": i["pos"], "addres": str(len(ASM) * 4)})
            for int32 in string_to_int32_array(i["value"]):
                ASM.append("WORD32 " + str(int32))
        else:
            print("compile_errors 1130")
            exit(1)

    ASM_info["START_ADR"] = len(ASM) * 4
    ASM[0] = "JMP " + str(len(ASM))
    for i in asm_datas:
        if i.type == "f":
            while asm_datas[0].value["offset"] % 4 != 0:
                asm_datas[0].value["offset"] += 1
            for j in range(i.value["offset"] // 4):
                i.value["asm"].insert(0, "PUSH 0")
                i.value["asm"].append("POP")
            if i.name == "":  # main
                i.value["asm"].append("HALT")
            else:
                i.value["asm"].append("RET")
    # print(global_const)
    # print(ASM);
    # for i in asm_datas:
    #    print(i.name, i.datatype, i.type, i.pos, i.is_global, i.value)
    linkFunction(asm_datas[0])
    # print(ASM);
    return ASM


def write_code(file_path, code):
    import json

    with open(file_path, "w") as file:
        json.dump(code, file)


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()
    tokens = tokenize(source)
    ast = build_ast(tokens)

    if ast_errors:
        for error in ast_errors:
            print(error)
        exit(1)
    ASM = compileAST(ast)
    # TODO variable is already defined + test in arg
    # TODO return in function
    if compile_errors:
        for error in compile_errors:
            print(error)
        exit(1)
    ASM = linkASM(ASM)
    write_code(target, ASM)
    print("source LoC:", len(source.split("\n")), "code instr:", len(ASM))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
